from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, TypeVar

import arro3.compute as ac
import numpy as np
from arro3.core import ChunkedArray, DataType, Scalar, Schema, list_flatten

from lonboard._compat import check_pandas_version
from lonboard._constants import EXTENSION_NAME, MIN_INTEGER_FLOAT32

if TYPE_CHECKING:
    from collections.abc import Sequence

    import geopandas as gpd
    import pandas as pd
    from numpy.typing import NDArray

    from lonboard._base import BaseExtension

    DF = TypeVar("DF", bound=pd.DataFrame)

GEOARROW_EXTENSION_TYPE_NAMES = {e.value for e in EXTENSION_NAME}


def get_geometry_column_index(schema: Schema) -> int | None:
    """Get the positional index of the geometry column in a pyarrow Schema."""
    field_idxs = []

    for field_idx in range(len(schema)):
        field_metadata = schema.field(field_idx).metadata
        if (
            field_metadata
            and field_metadata.get(b"ARROW:extension:name")
            in GEOARROW_EXTENSION_TYPE_NAMES
        ):
            field_idxs.append(field_idx)

    if len(field_idxs) > 1:
        raise ValueError("Multiple geometry columns not supported.")
    if len(field_idxs) == 1:
        return field_idxs[0]
    return None


def auto_downcast(df: DF) -> DF:
    """Automatically downcast types to smallest data size.

    Args:
        df: pandas DataFrame or geopandas GeoDataFrame

    Returns:
        DataFrame with downcasted data types

    """
    import pandas as pd

    check_pandas_version()

    # Convert objects to numeric types where possible.
    # Note: we have to exclude geometry because
    # `convert_dtypes(dtype_backend="pyarrow")` fails on the geometory column, but we
    # also have to manually cast to a non-geo data frame because it'll fail to convert
    # dtypes on a GeoDataFrame without a geom col
    casted_df = pd.DataFrame(df.select_dtypes(exclude="geometry")).convert_dtypes(  # type: ignore
        infer_objects=True,
        convert_string=True,
        convert_integer=True,
        convert_boolean=True,
        convert_floating=True,
        dtype_backend="pyarrow",
    )
    df[casted_df.columns] = casted_df

    # Try to convert _all_ integer columns to unsigned integer columns, but use
    # errors='ignore' to return signed integer data types for columns with negative
    # integers.
    for col_name in df.select_dtypes(np.integer).columns:  # type: ignore
        with contextlib.suppress(Exception):
            df[col_name] = pd.to_numeric(
                df[col_name],
                downcast="unsigned",
                dtype_backend="pyarrow",
            )

    # For any integer columns that are still signed integer, downcast those to smaller
    # signed types
    for col_name in df.select_dtypes(np.signedinteger).columns:  # type: ignore
        with contextlib.suppress(Exception):
            df[col_name] = pd.to_numeric(
                df[col_name],
                downcast="signed",
                dtype_backend="pyarrow",
            )

    for col_name in df.select_dtypes(np.floating).columns:  # type: ignore
        with contextlib.suppress(Exception):
            df[col_name] = pd.to_numeric(
                df[col_name],
                downcast="float",
                dtype_backend="pyarrow",
            )

    return df


def remove_extension_kwargs(
    extensions: Sequence[BaseExtension],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Remove extension properties from kwargs, returning the removed properties.

    **This mutates the kwargs input.**
    """
    extension_kwargs: dict[str, Any] = {}
    if extensions:
        for extension in extensions:
            for extension_prop_name in extension._layer_traits:  # noqa: SLF001
                if extension_prop_name in kwargs:
                    extension_kwargs[extension_prop_name] = kwargs.pop(
                        extension_prop_name,
                    )

    return extension_kwargs


def split_mixed_gdf(gdf: gpd.GeoDataFrame) -> list[gpd.GeoDataFrame]:
    """Split a GeoDataFrame into one or more GeoDataFrames with unique geometry type."""
    indices = indices_by_geometry_type(gdf.geometry)
    if indices is None:
        return [gdf]

    point_indices, linestring_indices, polygon_indices = indices

    # Here we intentionally check geometries in a specific order.
    # Starting from polygons, then linestrings, then points,
    # so that the order of generated layers is polygon, then path then scatterplot.
    # This ensures that points are rendered on top and polygons on the bottom.
    gdfs = []
    for single_type_geometry_indices in (
        polygon_indices,
        linestring_indices,
        point_indices,
    ):
        if len(single_type_geometry_indices) > 0:
            gdfs.append(gdf.iloc[single_type_geometry_indices])

    return gdfs


def split_mixed_shapely_array(
    geometry: NDArray[np.object_],
) -> list[NDArray[np.object_]]:
    """Split a shapely array into one or more arrays with unique geometry type."""
    indices = indices_by_geometry_type(geometry)
    if indices is None:
        return [geometry]

    point_indices, linestring_indices, polygon_indices = indices

    # Here we intentionally check geometries in a specific order.
    # Starting from polygons, then linestrings, then points,
    # so that the order of generated layers is polygon, then path then scatterplot.
    # This ensures that points are rendered on top and polygons on the bottom.
    arrays = []
    for single_type_geometry_indices in (
        polygon_indices,
        linestring_indices,
        point_indices,
    ):
        if len(single_type_geometry_indices) > 0:
            arrays.append(geometry[single_type_geometry_indices])

    return arrays


def indices_by_geometry_type(
    geometry: NDArray[np.object_],
) -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.int64]] | None:
    import shapely
    from shapely import GeometryType

    type_ids = np.array(shapely.get_type_id(geometry))
    unique_type_ids = set(np.unique(type_ids))

    if GeometryType.GEOMETRYCOLLECTION in unique_type_ids:
        raise ValueError("GeometryCollections not currently supported")

    if GeometryType.LINEARRING in unique_type_ids:
        raise ValueError("LinearRings not currently supported")

    if len(unique_type_ids) == 1:
        return None

    if len(unique_type_ids) == 2:
        if unique_type_ids == {GeometryType.POINT, GeometryType.MULTIPOINT}:
            return None

        if unique_type_ids == {GeometryType.LINESTRING, GeometryType.MULTILINESTRING}:
            return None

        if unique_type_ids == {GeometryType.POLYGON, GeometryType.MULTIPOLYGON}:
            return None

    point_indices = np.where(
        (type_ids == GeometryType.POINT) | (type_ids == GeometryType.MULTIPOINT),
    )[0]

    linestring_indices = np.where(
        (type_ids == GeometryType.LINESTRING)
        | (type_ids == GeometryType.MULTILINESTRING),
    )[0]

    polygon_indices = np.where(
        (type_ids == GeometryType.POLYGON) | (type_ids == GeometryType.MULTIPOLYGON),
    )[0]

    return point_indices, linestring_indices, polygon_indices


def timestamp_start_offset(timestamps: ChunkedArray) -> int:
    timestamps = timestamps.cast(DataType.list(DataType.int64()))

    min_timestamp = ac.min(list_flatten(timestamps))
    return MIN_INTEGER_FLOAT32 - min_timestamp.as_py()


def timestamp_max_physical_value(timestamps: ChunkedArray) -> int:
    # Cast to int64 type
    timestamps = timestamps.cast(DataType.list(DataType.int64()))

    min_timestamp = ac.min(list_flatten(timestamps))
    max_timestamp = ac.max(list_flatten(timestamps))
    start_offset_adjustment = Scalar(
        MIN_INTEGER_FLOAT32 - min_timestamp.as_py(),
        type=DataType.int64(),
    )
    return start_offset_adjustment.as_py() + max_timestamp.as_py()

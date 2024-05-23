from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, TypeVar

import numpy as np
import pandas as pd
import pyarrow as pa
import shapely
from shapely import GeometryType

from lonboard._base import BaseExtension
from lonboard._constants import EXTENSION_NAME

if TYPE_CHECKING:
    import geopandas as gpd

DF = TypeVar("DF", bound=pd.DataFrame)

GEOARROW_EXTENSION_TYPE_NAMES = {e.value for e in EXTENSION_NAME}


def get_geometry_column_index(schema: pa.Schema) -> Optional[int]:
    """Get the positional index of the geometry column in a pyarrow Schema"""
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
    elif len(field_idxs) == 1:
        return field_idxs[0]
    else:
        return None


def auto_downcast(df: DF) -> DF:
    """Automatically downcast types to smallest data size

    Args:
        df: pandas DataFrame or geopandas GeoDataFrame

    Returns:
        DataFrame with downcasted data types
    """
    # Convert objects to numeric types where possible.
    # Note: we have to exclude geometry because
    # `convert_dtypes(dtype_backend="pyarrow")` fails on the geometory column, but we
    # also have to manually cast to a non-geo data frame because it'll fail to convert
    # dtypes on a GeoDataFrame without a geom col
    casted_df = pd.DataFrame(df.select_dtypes(exclude="geometry")).convert_dtypes(
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
        try:
            df[col_name] = pd.to_numeric(
                df[col_name], downcast="unsigned", dtype_backend="pyarrow"
            )
        except Exception:
            pass

    # For any integer columns that are still signed integer, downcast those to smaller
    # signed types
    for col_name in df.select_dtypes(np.signedinteger).columns:  # type: ignore
        try:
            df[col_name] = pd.to_numeric(
                df[col_name], downcast="signed", dtype_backend="pyarrow"
            )
        except Exception:
            pass

    for col_name in df.select_dtypes(np.floating).columns:  # type: ignore
        try:
            df[col_name] = pd.to_numeric(
                df[col_name], downcast="float", dtype_backend="pyarrow"
            )
        except Exception:
            pass

    return df


def remove_extension_kwargs(
    extensions: Sequence[BaseExtension], kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """Remove extension properties from kwargs, returning the removed properties.

    **This mutates the kwargs input.**
    """
    extension_kwargs: Dict[str, Any] = {}
    if extensions:
        for extension in extensions:
            for extension_prop_name in extension._layer_traits.keys():
                if extension_prop_name in kwargs:
                    extension_kwargs[extension_prop_name] = kwargs.pop(
                        extension_prop_name
                    )

    return extension_kwargs


def split_mixed_gdf(gdf: gpd.GeoDataFrame) -> List[gpd.GeoDataFrame]:
    """Split a GeoDataFrame into one or more GeoDataFrames with unique geometry type"""

    type_ids = np.array(shapely.get_type_id(gdf.geometry))
    unique_type_ids = set(np.unique(type_ids))

    if GeometryType.GEOMETRYCOLLECTION in unique_type_ids:
        raise ValueError("GeometryCollections not currently supported")

    if GeometryType.LINEARRING in unique_type_ids:
        raise ValueError("LinearRings not currently supported")

    if len(unique_type_ids) == 1:
        return [gdf]

    if len(unique_type_ids) == 2:
        if unique_type_ids == {GeometryType.POINT, GeometryType.MULTIPOINT}:
            return [gdf]

        if unique_type_ids == {GeometryType.LINESTRING, GeometryType.MULTILINESTRING}:
            return [gdf]

        if unique_type_ids == {GeometryType.POLYGON, GeometryType.MULTIPOLYGON}:
            return [gdf]

    point_indices = np.where(
        (type_ids == GeometryType.POINT) | (type_ids == GeometryType.MULTIPOINT)
    )[0]

    linestring_indices = np.where(
        (type_ids == GeometryType.LINESTRING)
        | (type_ids == GeometryType.MULTILINESTRING)
    )[0]

    polygon_indices = np.where(
        (type_ids == GeometryType.POLYGON) | (type_ids == GeometryType.MULTIPOLYGON)
    )[0]

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

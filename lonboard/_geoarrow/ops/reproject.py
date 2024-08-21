"""Reproject a GeoArrow array"""

import json
import warnings
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache, partial
from typing import Callable, Optional, Tuple, Union
from warnings import warn

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    Field,
    Table,
    fixed_size_list_array,
    list_array,
    list_flatten,
    list_offsets,
)
from pyproj import CRS, Transformer

from lonboard._constants import EPSG_4326, EXTENSION_NAME, OGC_84
from lonboard._geoarrow.crs import get_field_crs
from lonboard._geoarrow.extension_types import CoordinateDimension
from lonboard._utils import get_geometry_column_index

TransformerFromCRS = lru_cache(Transformer.from_crs)


def no_crs_warning():
    warn(
        "No CRS exists on data. "
        "If no data is shown on the map, double check that your CRS is WGS84."
    )


def reproject_table(
    table: Table,
    *,
    to_crs: Union[str, CRS] = OGC_84,
    max_workers: Optional[int] = None,
) -> Table:
    """Reproject a GeoArrow table to a new CRS

    Args:
        table: The table to reproject.
        to_crs: The target CRS. Defaults to OGC_84.
        max_workers: The maximum number of threads to use. Defaults to None.

    Returns:
        A new table.
    """
    geom_col_idx = get_geometry_column_index(table.schema)
    # No geometry column in table
    if geom_col_idx is None:
        return table

    geom_field = table.schema.field(geom_col_idx)
    geom_column = table.column(geom_col_idx)

    # geometry column exists in table but is not assigned a CRS
    if b"ARROW:extension:metadata" not in geom_field.metadata:
        no_crs_warning()
        return table

    new_field, new_column = reproject_column(
        field=geom_field, column=geom_column, to_crs=to_crs, max_workers=max_workers
    )
    return table.set_column(geom_col_idx, new_field, new_column)


def reproject_column(
    *,
    field: Field,
    column: ChunkedArray,
    to_crs: Union[str, CRS] = OGC_84,
    max_workers: Optional[int] = None,
) -> Tuple[Field, ChunkedArray]:
    """Reproject a GeoArrow array to a new CRS

    Args:
        field: The field describing the column
        column: A ChunkedArray
        to_crs: The target CRS. Defaults to OGC_84.
        max_workers: The maximum number of threads to use. Defaults to None.
    """
    extension_type_name = field.metadata[b"ARROW:extension:name"]
    crs_str = get_field_crs(field)
    if crs_str is None:
        no_crs_warning()
        return field, column

    existing_crs = CRS(crs_str)

    if existing_crs == to_crs:
        return field, column

    # If projecting to OGC_84, also check if existing CRS is EPSG_4326, which when
    # passing always_xy is equivalent.
    if to_crs == OGC_84:
        if existing_crs == EPSG_4326:
            return field, column

    # NOTE: Not sure the best place to put this warning
    warnings.warn("Input being reprojected to EPSG:4326 CRS")

    transformer = TransformerFromCRS(existing_crs, to_crs, always_xy=True)

    # Metadata inside metadata, bad naming
    new_extension_meta_meta = {"crs": CRS(to_crs).to_json()}
    new_extension_metadata = {
        b"ARROW:extension:name": extension_type_name,
        b"ARROW:extension:metadata": json.dumps(new_extension_meta_meta).encode(),
    }

    new_chunked_array = _reproject_column(
        column,
        extension_type_name=extension_type_name,  # type: ignore
        transformer=transformer,
        max_workers=max_workers,
    )
    new_field = field.with_type(new_chunked_array.type).with_metadata(
        new_extension_metadata
    )
    return new_field, new_chunked_array


def _reproject_column(
    column: ChunkedArray,
    *,
    extension_type_name: EXTENSION_NAME,
    transformer: Transformer,
    max_workers: Optional[int] = None,
) -> ChunkedArray:
    if extension_type_name == EXTENSION_NAME.POINT:
        func = partial(_reproject_chunk_nest_0, transformer=transformer)
    elif extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        func = partial(_reproject_chunk_nest_1, transformer=transformer)
    elif extension_type_name in [
        EXTENSION_NAME.POLYGON,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        func = partial(_reproject_chunk_nest_2, transformer=transformer)

    elif extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        func = partial(_reproject_chunk_nest_3, transformer=transformer)
    else:
        raise ValueError(f"Unexpected extension type name {extension_type_name}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return ChunkedArray(list(executor.map(func, column.chunks)))


def _reproject_coords(arr: Array, transformer: Transformer):
    list_size = arr.type.list_size
    assert list_size is not None
    np_arr = list_flatten(arr).to_numpy().reshape(-1, list_size)

    if list_size == 2:
        output_np_arr = np.column_stack(
            transformer.transform(np_arr[:, 0], np_arr[:, 1])
        )
        dims = CoordinateDimension.XY
    elif list_size == 3:
        output_np_arr = np.column_stack(
            transformer.transform(np_arr[:, 0], np_arr[:, 1], np_arr[:, 2])
        )
        dims = CoordinateDimension.XYZ
    else:
        raise ValueError(f"Unexpected list size {list_size}")

    coord_field = DataType.list(Field(dims, DataType.float64()), len(dims))
    return fixed_size_list_array(
        Array.from_numpy(output_np_arr.ravel("C")),
        len(dims),
        type=coord_field,
    )


def _reproject_chunk_nest_0(arr: Array, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_0(arr, callback)


def _reproject_chunk_nest_1(arr: Array, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_1(arr, callback)


def _reproject_chunk_nest_2(arr: Array, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_2(arr, callback)


def _reproject_chunk_nest_3(arr: Array, transformer: Transformer):
    callback = partial(_reproject_coords, transformer=transformer)
    return _map_coords_nest_3(arr, callback)


def _map_coords_nest_0(
    arr: Array,
    callback: Callable[[Array], Array],
) -> Array:
    new_coords = callback(arr)
    return new_coords


def _map_coords_nest_1(
    arr: Array,
    callback: Callable[[Array], Array],
) -> Array:
    geom_offsets = list_offsets(arr, logical=True)
    coords = list_flatten(arr)
    new_coords = callback(coords)
    new_geometry_array = list_array(geom_offsets, new_coords)
    return new_geometry_array


def _map_coords_nest_2(
    arr: Array,
    callback: Callable[[Array], Array],
):
    geom_offsets = list_offsets(arr, logical=True)
    ring_offsets = list_offsets(list_flatten(arr), logical=True)
    coords = list_flatten(list_flatten(arr))
    new_coords = callback(coords)
    new_ring_array = list_array(ring_offsets, new_coords)
    new_geometry_array = list_array(geom_offsets, new_ring_array)
    return new_geometry_array


def _map_coords_nest_3(
    arr: Array,
    callback: Callable[[Array], Array],
):
    geom_offsets = list_offsets(arr, logical=True)
    polygon_offsets = list_offsets(list_flatten(arr), logical=True)
    ring_offsets = list_offsets(list_flatten(list_flatten(arr)), logical=True)
    coords = list_flatten(list_flatten(list_flatten(arr)))
    new_coords = callback(coords)
    new_ring_array = list_array(ring_offsets, new_coords)
    new_polygon_array = list_array(polygon_offsets, new_ring_array)
    new_geometry_array = list_array(geom_offsets, new_polygon_array)
    return new_geometry_array

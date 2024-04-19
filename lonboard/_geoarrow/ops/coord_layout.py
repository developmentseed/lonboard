"""Convert a GeoArrow array to interleaved representation"""

from typing import Tuple, Union

import numpy as np
import pyarrow as pa

from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.ops.reproject import (
    _map_coords_nest_0,
    _map_coords_nest_1,
    _map_coords_nest_2,
    _map_coords_nest_3,
)
from lonboard._utils import get_geometry_column_index


def transpose_table(
    table: pa.Table,
) -> pa.Table:
    """Convert geometry columns in table to interleaved coordinate layout"""
    geom_col_idx = get_geometry_column_index(table.schema)
    # No geometry column in table
    if geom_col_idx is None:
        return table

    geom_field = table.schema.field(geom_col_idx)
    geom_column = table.column(geom_col_idx)

    new_field, new_column = transpose_column(field=geom_field, column=geom_column)
    return table.set_column(geom_col_idx, new_field, new_column)


def transpose_column(
    *,
    field: pa.Field,
    column: pa.ChunkedArray,
) -> Tuple[pa.Field, pa.ChunkedArray]:
    extension_type_name = field.metadata[b"ARROW:extension:name"]

    new_chunked_array = _transpose_column(
        column,
        extension_type_name=extension_type_name,
    )
    return field.with_type(new_chunked_array.type), new_chunked_array


def _transpose_column(
    column: pa.ChunkedArray,
    *,
    extension_type_name: EXTENSION_NAME,
) -> pa.ChunkedArray:
    if extension_type_name == EXTENSION_NAME.POINT:
        func = _transpose_chunk_nest_0
    elif extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        func = _transpose_chunk_nest_1
    elif extension_type_name in [
        EXTENSION_NAME.POLYGON,
        EXTENSION_NAME.MULTILINESTRING,
    ]:
        func = _transpose_chunk_nest_2

    elif extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        func = _transpose_chunk_nest_3
    else:
        raise ValueError(f"Unexpected extension type name {extension_type_name}")

    return pa.chunked_array([func(chunk) for chunk in column.chunks])


def _transpose_coords(arr: Union[pa.FixedSizeListArray, pa.StructArray]):
    if isinstance(arr, pa.FixedSizeListArray):
        return arr

    if arr.type.num_fields == 2:
        x = arr.field("x").to_numpy()
        y = arr.field("y").to_numpy()
        coords = np.column_stack([x, y]).flatten("C")
        return pa.FixedSizeListArray.from_arrays(coords, 2)

    if arr.type.num_fields == 3:
        x = arr.field("x").to_numpy()
        y = arr.field("y").to_numpy()
        z = arr.field("z").to_numpy()
        coords = np.column_stack([x, y, z]).flatten("C")
        return pa.FixedSizeListArray.from_arrays(coords, 3)

    raise ValueError(f"Expected struct with 2 or 3 fields, got {arr.type.num_fields}")


def _transpose_chunk_nest_0(arr: pa.ListArray):
    return _map_coords_nest_0(arr, _transpose_coords)


def _transpose_chunk_nest_1(arr: pa.ListArray):
    return _map_coords_nest_1(arr, _transpose_coords)


def _transpose_chunk_nest_2(arr: pa.ListArray):
    return _map_coords_nest_2(arr, _transpose_coords)


def _transpose_chunk_nest_3(arr: pa.ListArray):
    return _map_coords_nest_3(arr, _transpose_coords)

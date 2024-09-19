"""Convert a GeoArrow array to interleaved representation"""

from typing import Tuple

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    Field,
    Table,
    fixed_size_list_array,
    struct_field,
)

from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.ops.reproject import (
    _map_coords_nest_0,
    _map_coords_nest_1,
    _map_coords_nest_2,
    _map_coords_nest_3,
)
from lonboard._utils import get_geometry_column_index


def transpose_table(
    table: Table,
) -> Table:
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
    field: Field,
    column: ChunkedArray,
) -> Tuple[Field, ChunkedArray]:
    extension_type_name = field.metadata[b"ARROW:extension:name"]

    new_chunked_array = _transpose_column(
        column,
        extension_type_name=extension_type_name,  # type: ignore
    )
    return field.with_type(new_chunked_array.type), new_chunked_array


def _transpose_column(
    column: ChunkedArray,
    *,
    extension_type_name: EXTENSION_NAME,
) -> ChunkedArray:
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

    return ChunkedArray([func(chunk) for chunk in column.chunks])


def _transpose_coords(arr: Array):
    if DataType.is_fixed_size_list(arr.type):
        return arr

    if arr.type.num_fields == 2:
        x = struct_field(arr, [0]).to_numpy()
        y = struct_field(arr, [1]).to_numpy()
        coords = np.column_stack([x, y]).ravel("C")
        flat_coords = Array.from_numpy(coords)
        return fixed_size_list_array(flat_coords, 2)

    if arr.type.num_fields == 3:
        x = struct_field(arr, [0]).to_numpy()
        y = struct_field(arr, [1]).to_numpy()
        z = struct_field(arr, [2]).to_numpy()
        coords = np.column_stack([x, y, z]).ravel("C")
        flat_coords = Array.from_numpy(coords)
        return fixed_size_list_array(flat_coords, 3)

    raise ValueError(f"Expected struct with 2 or 3 fields, got {arr.type.num_fields}")


def _transpose_chunk_nest_0(arr: Array):
    return _map_coords_nest_0(arr, _transpose_coords)


def _transpose_chunk_nest_1(arr: Array):
    return _map_coords_nest_1(arr, _transpose_coords)


def _transpose_chunk_nest_2(arr: Array):
    return _map_coords_nest_2(arr, _transpose_coords)


def _transpose_chunk_nest_3(arr: Array):
    return _map_coords_nest_3(arr, _transpose_coords)

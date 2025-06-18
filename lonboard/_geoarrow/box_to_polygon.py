"""Convert geoarrow.box arrays to geoarrow.polygon arrays."""

from __future__ import annotations

from typing import overload

import numpy as np
from arro3.core import (
    Array,
    ChunkedArray,
    Field,
    Schema,
    Table,
    fixed_size_list_array,
    list_array,
    struct_field,
)

from lonboard._geoarrow.extension_types import CoordinateDimension


@overload
def box_to_polygon(array: Array) -> Array: ...
@overload
def box_to_polygon(array: ChunkedArray) -> ChunkedArray: ...
def box_to_polygon(array: Array | ChunkedArray) -> Array | ChunkedArray:
    """Convert geoarrow.box arrays to geoarrow.polygon arrays."""
    if isinstance(array, ChunkedArray):
        return ChunkedArray([box_to_polygon(chunk) for chunk in array.chunks])

    if array.field.metadata_str["ARROW:extension:name"] != "geoarrow.box":
        raise ValueError(
            f"Expected geoarrow.box array in box_to_polygon, got {array.field.metadata_str['ARROW:extension:name']}",
        )

    if array.null_count > 0:
        raise ValueError("box_to_polygon does not currently support null values.")

    # Released arro3 doesn't have a way to get the children of the struct field
    # We check the number of child fields to infer the positions of the 2D bbox fields
    if array.type.num_fields == 4:
        xmin = struct_field(array, 0)
        ymin = struct_field(array, 1)
        xmax = struct_field(array, 2)
        ymax = struct_field(array, 3)
    elif array.type.num_fields == 6:
        xmin = struct_field(array, 0)
        ymin = struct_field(array, 1)
        xmax = struct_field(array, 3)
        ymax = struct_field(array, 4)
    elif array.type.num_fields == 8:
        xmin = struct_field(array, 0)
        ymin = struct_field(array, 1)
        xmax = struct_field(array, 4)
        ymax = struct_field(array, 5)
    else:
        raise ValueError(
            f"Unsupported number of fields in geoarrow.box array: {array.type.num_fields}",
        )

    # TODO: handle null values in the box array
    polygon_coords = np.zeros((len(array), 5, 2), dtype=np.float64)

    # https://github.com/geoarrow/geoarrow-rs/blob/c8561fb61bd21a4455a7b7741bf80a6935ae6060/rust/geoarrow-array/src/builder/geo_trait_wrappers.rs#L172-L181
    # ll, ul, ur, lr, ll
    polygon_coords[:, 0, 0] = xmin
    polygon_coords[:, 0, 1] = ymin

    polygon_coords[:, 1, 0] = xmin
    polygon_coords[:, 1, 1] = ymax

    polygon_coords[:, 2, 0] = xmax
    polygon_coords[:, 2, 1] = ymax

    polygon_coords[:, 3, 0] = xmax
    polygon_coords[:, 3, 1] = ymin

    polygon_coords[:, 4, 0] = xmin
    polygon_coords[:, 4, 1] = ymin

    ring_offsets = np.arange((len(array) + 1) * 5, step=5, dtype=np.int32)
    geom_offsets = np.arange(len(array) + 1, dtype=np.int32)

    arrow_coords = fixed_size_list_array(
        polygon_coords.ravel("C"),
        len(CoordinateDimension.XY),
    )
    arrow_rings = list_array(ring_offsets, arrow_coords)
    return list_array(geom_offsets, arrow_rings)


def parse_box_encoded_table(table: Table) -> Table:
    """Convert a table with a geoarrow.box column into a table with a geoarrow.polygon column."""
    # Find the index of the box column
    box_col_idx = None
    for idx in range(len(table.schema)):
        field = table.schema.field(idx)
        if field.metadata_str.get("ARROW:extension:name") == "geoarrow.box":
            if box_col_idx is not None:
                raise ValueError("Multiple geoarrow.box columns found in the table.")

            box_col_idx = idx

    if box_col_idx is None:
        # No box column found, return the table unchanged
        return table

    # Convert the box column to a polygon column
    box_col = table.column(box_col_idx)
    polygon_col = box_to_polygon(box_col)

    new_metadata = box_col.field.metadata_str.copy()
    new_metadata["ARROW:extension:name"] = "geoarrow.polygon"
    new_field = Field(
        name=box_col.field.name,
        type=polygon_col.type,
        nullable=box_col.field.nullable,
        metadata=new_metadata,
    )

    fields = list(iter(table.schema))
    fields[box_col_idx] = new_field
    new_schema = Schema(fields, metadata=table.schema.metadata)

    return table.set_column(
        box_col_idx,
        new_field,
        polygon_col,
    ).with_schema(new_schema)

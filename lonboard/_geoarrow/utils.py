from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from arro3.core import Array, DataType, Table, fixed_size_list_array

from lonboard._constants import EXTENSION_NAME
from lonboard._utils import get_geometry_column_index

if TYPE_CHECKING:
    from arro3.core import Field


def fixed_size_list_from_numpy(
    values: np.ndarray,
    list_size: int,
    *,
    type: DataType | Field | None = None,  # noqa: A002
) -> Array:
    """Construct a FixedSizeList array from a flat numpy array.

    Unlike `arro3.core.fixed_size_list_array`, this also accepts zero-length input
    (such as the coordinates of empty geometries), which arro3 can't yet import from
    numpy. This can be removed once arro3 supports it:
    https://github.com/kylebarron/arro3/issues/519
    """
    if values.size == 0:
        # Slice a one-element Arrow array to zero length to keep the numpy dtype
        return fixed_size_list_array(
            Array(np.zeros(1, dtype=values.dtype)).slice(0, 0),
            list_size,
            type=type,
        )

    return fixed_size_list_array(values, list_size, type=type)


def drop_nan_coords(coords: np.ndarray) -> np.ndarray:
    """Remove rows of a 2D coordinate array that contain NaN.

    GeoArrow stores an empty point as a coordinate of NaN values.
    """
    has_nan = np.isnan(coords).any(axis=1)
    if not has_nan.any():
        return coords

    return coords[~has_nan]


def remove_empty_batches(table: Table) -> Table:
    """Remove record batches with no rows from a table."""
    batches = [batch for batch in table.to_batches() if batch.num_rows > 0]
    return Table.from_batches(batches, schema=table.schema)


def is_primitive_geoarrow(field: Field) -> bool:
    """Return True if this GeoArrow column is in a "primitive" coordinate representation.

    "Primitive" means both that it is "native" (i.e. not WKB or WKT) and that it
    is a single geometry type (e.g. Point, LineString, Polygon, etc.).

    This will return false for WKB and WKT-serialized arrays. This will also return
    False for Geometry and GeometryCollection type arrays.
    """
    return field.metadata.get(b"ARROW:extension:name") in {
        EXTENSION_NAME.POINT,
        EXTENSION_NAME.LINESTRING,
        EXTENSION_NAME.POLYGON,
        EXTENSION_NAME.MULTIPOINT,
        EXTENSION_NAME.MULTILINESTRING,
        EXTENSION_NAME.MULTIPOLYGON,
        EXTENSION_NAME.BOX,
    }


def check_float_coords(table: Table) -> None:
    """Raise if the geometry column of a table has coordinates that aren't floating point.

    GeoArrow requires floating point coordinates, and integer coordinates render
    nothing: https://github.com/developmentseed/lonboard/issues/608

    Only native GeoArrow columns are checked. WKB and WKT columns don't have a
    coordinate type until they're parsed.
    """
    geom_col_idx = get_geometry_column_index(table.schema)
    if geom_col_idx is None:
        return

    field = table.schema.field(geom_col_idx)
    if not is_primitive_geoarrow(field):
        return

    # Descend through the lists around the coordinates, including the fixed size list
    # of interleaved coordinates
    typ = field.type
    while typ.value_type is not None:
        typ = typ.value_type

    # Separated coordinates and boxes are a struct with one field per dimension
    coord_types = [f.type for f in typ.fields] if DataType.is_struct(typ) else [typ]

    for coord_type in coord_types:
        if not DataType.is_floating(coord_type):
            raise ValueError(
                "GeoArrow coordinates must be floating point, got "
                f"{str(coord_type).strip()}. Cast the coordinates to float64.",
            )

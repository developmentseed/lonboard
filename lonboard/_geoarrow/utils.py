from __future__ import annotations

from typing import TYPE_CHECKING

from lonboard._constants import EXTENSION_NAME

if TYPE_CHECKING:
    from arro3.core import Field


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

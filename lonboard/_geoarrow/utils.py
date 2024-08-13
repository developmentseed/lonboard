from __future__ import annotations

from lonboard._constants import EXTENSION_NAME


def is_native_geoarrow(extension_type_name: bytes | None) -> bool:
    """Return True if this GeoArrow column has a "native" coordinate representation

    This will return false for WKB and WKT-serialized arrays.
    """
    return extension_type_name not in {
        EXTENSION_NAME.WKB,
        EXTENSION_NAME.OGC_WKB,
        EXTENSION_NAME.WKT,
    }

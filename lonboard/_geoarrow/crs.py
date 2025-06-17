from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyproj import CRS

if TYPE_CHECKING:
    from arro3.core import Field


# Note: According to the spec, if the metadata key exists, its value should never be
# `null` or an empty dict, but we still check for those to be safe
def get_field_crs(field: Field) -> CRS | None:
    extension_metadata_value = field.metadata_str.get("ARROW:extension:metadata")
    if not extension_metadata_value:
        return None

    extension_metadata = json.loads(extension_metadata_value)
    return parse_metadata(extension_metadata)


def parse_metadata(extension_metadata: dict[str, Any]) -> CRS | None:
    crs_val = extension_metadata.get("crs")
    crs_type = extension_metadata.get("crs_type")

    if crs_type == "projjson":
        assert crs_val is not None, "CRS value must be provided for projjson type"
        return CRS.from_json_dict(crs_val)

    if crs_type == "wkt2:2019":
        assert crs_val is not None, "CRS value must be provided for WKT2:2019 type"
        return CRS.from_wkt(crs_val)

    if crs_type == "authority_code":
        assert crs_val is not None, "CRS value must be provided for authority code type"
        assert ":" in crs_val, "Authority code must be in the format 'authority:code'"
        assert isinstance(crs_val, str), "CRS value must be a string"
        return CRS.from_authority(*crs_val.split(":", 1))

    return CRS.from_user_input(crs_val) if crs_val is not None else None


def serialize_crs(crs: CRS | None) -> dict[str, Any] | None:
    """Serialize a CRS to GeoArrow metadata.

    The returned GeoArrow metadata should be JSON-serialized within the
    ARROW:extension:metadata key.
    """
    if crs is None:
        return None

    return {
        "crs": crs.to_json_dict(),
        "crs_type": "projjson",
    }

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arro3.core import Field


# Note: According to the spec, if the metadata key exists, its value should never be
# `null` or an empty dict, but we still check for those to be safe
def get_field_crs(field: Field) -> dict | None:
    extension_metadata_value = field.metadata.get(b"ARROW:extension:metadata")
    if not extension_metadata_value:
        return None

    extension_metadata = json.loads(extension_metadata_value)
    return extension_metadata.get("crs")

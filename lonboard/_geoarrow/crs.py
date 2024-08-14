import json
from typing import Optional

from arro3.core import Field


# Note: According to the spec, if the metadata key exists, its value should never be
# `null` or an empty dict, but we still check for those to be safe
def get_field_crs(field: Field) -> Optional[str]:
    extension_metadata_value = field.metadata.get(b"ARROW:extension:metadata")
    if not extension_metadata_value:
        return None

    extension_metadata = json.loads(extension_metadata_value)
    return extension_metadata.get("crs")

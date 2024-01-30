"""Remove custom geoarrow.pyarrow types from input geoarrow data
"""
import json
from typing import Tuple

import pyarrow as pa
from pyproj import CRS


def sanitize_table(table: pa.Table) -> pa.Table:
    """
    Convert any registered geoarrow.pyarrow extension fields and arrays to plain
    metadata
    """
    for field_idx in range(len(table.schema)):
        field = table.field(field_idx)
        column = table.column(field_idx)

        if isinstance(field.type, pa.ExtensionType):
            assert all(isinstance(chunk, pa.ExtensionArray) for chunk in column.chunks)
            new_field, new_column = sanitize_column(field, column)
            table = table.set_column(field_idx, new_field, new_column)

    return table


def sanitize_column(
    field: pa.Field, column: pa.ChunkedArray
) -> Tuple[pa.Field, pa.ChunkedArray]:
    """
    Convert a registered geoarrow.pyarrow extension field and column to plain metadata
    """
    import geoarrow.pyarrow as gap

    extension_metadata = {}
    if field.type.crs:
        extension_metadata["crs"] = CRS.from_user_input(field.type.crs).to_json()

    if field.type.edge_type == gap.EdgeType.SPHERICAL:
        extension_metadata["edges"] = "spherical"

    metadata = {
        "ARROW:extension:name": field.type.extension_name,
    }
    if extension_metadata:
        metadata["ARROW:extension:metadata"] = json.dumps(extension_metadata)

    new_field = pa.field(
        field.name, field.type.storage_type, nullable=field.nullable, metadata=metadata
    )

    new_chunks = []
    for chunk in column.chunks:
        if hasattr(chunk, "storage"):
            new_chunks.append(chunk.storage)
        else:
            new_chunks.append(chunk.cast(new_field.type))

    return new_field, pa.chunked_array(new_chunks)

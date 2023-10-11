import pyarrow as pa

GEOARROW_EXTENSION_TYPE_NAMES = {
    b"geoarrow.point",
    b"geoarrow.linestring",
    b"geoarrow.polygon",
    b"geoarrow.multipoint",
    b"geoarrow.multilinestring",
    b"geoarrow.multipolygon",
}


def get_geometry_column_index(schema: pa.Schema) -> int:
    """Get the positional index of the geometry column in a pyarrow Schema"""
    for field_idx in range(len(schema)):
        field_metadata = schema.field(field_idx).metadata
        if (
            field_metadata
            and field_metadata.get(b"ARROW:extension:name")
            in GEOARROW_EXTENSION_TYPE_NAMES
        ):
            return field_idx

    raise ValueError("No geometry column in table schema.")

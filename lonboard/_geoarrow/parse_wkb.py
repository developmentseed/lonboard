"""Handle GeoArrow tables with WKB-encoded geometry."""

import json

import numpy as np
from arro3.core import Field, Table
from geoarrow.rust.core import GeoChunkedArray, get_type_id

from lonboard._constants import EXTENSION_NAME, OGC_84
from lonboard._geoarrow.utils import is_primitive_geoarrow
from lonboard._utils import get_geometry_column_index

# Here we intentionally check geometries in a specific order.
# Starting from polygons, then linestrings, then points,
# so that the order of generated layers is polygon, then path then scatterplot.
# This ensures that points are rendered on top and polygons on the bottom.
#
# We can merge Point/LineString/Polygon and their Multi* counterparts, but we don't
# currently merge across dimension
TYPE_ID_ORDERING = [
    (16, 13),  # MultiPolygon Z, Polygon Z
    (6, 3),  # MultiPolygon, Polygon
    (15, 12),  # MultiLineString Z, LineString Z
    (5, 2),  # MultiLineString, LineString
    (14, 11),  # MultiPoint Z, Point Z
    (4, 1),  # MultiPoint, Point
]


def parse_serialized_table(table: Table) -> list[Table]:
    """Parse a table with a serialized WKB/WKT column into GeoArrow-native geometries.

    If no columns are WKB/WKT-encoded, returns the input. Note that WKB columns must be
    tagged with an extension name of `geoarrow.wkb` or `ogc.wkb`. WKT columns must be
    tagged with an extension name of `geoarrow.wkt`.

    Returns one table per GeoArrow geometry type. E.g. if the input has points, lines,
    and polygons, then it returns three tables. Point/MultiPoint,
    LineString/MultiLineString, Polygon/MultiPolygon are each combined into a single
    table type.
    """
    table = parse_geoparquet_table(table)
    field_idx = get_geometry_column_index(table.schema)

    # For non-geometry table, just return as-is
    if field_idx is None:
        return [table]

    field = table.field(field_idx)
    column = table.column(field_idx)

    # For native GeoArrow input, return table as-is
    # We need to downcast wkb/wkt/geometry
    if is_primitive_geoarrow(field):
        return [table]

    type_ids = get_type_id(column).read_all()
    unique_type_ids = {int(type_id) for type_id in np.asarray(type_ids)}
    if any(type_id >= 20 for type_id in unique_type_ids):
        raise ValueError(
            "Lonboard does not currently support M dimensional geometries.",
        )
    if any(type_id % 10 == 7 for type_id in unique_type_ids):
        raise ValueError(
            "Lonboard does not currently support GeometryCollections.",
        )

    # If there's a single type id, then we know we can downcast to that specific type.
    # In this case the input geometry is either WKB, WKT, or Geometry.
    if len(unique_type_ids) == 1:
        return [single_type_id_downcast(table)]

    type_ids_np = np.asarray(type_ids)

    parsed_tables: list[Table] = []
    concatted_batch = table.combine_chunks().to_batches()[0]

    for type_id_pair in TYPE_ID_ORDERING:
        if unique_type_ids.intersection(type_id_pair):
            indices = np.where(
                np.logical_or(
                    type_ids_np == type_id_pair[0],
                    type_ids_np == type_id_pair[1],
                ),
            )[0]
            assert len(indices) > 0, "Expected to find some geometries of this type."
            selected = concatted_batch.take(indices)
            parsed_tables.append(
                single_type_id_downcast(Table.from_batches([selected])),
            )

    return parsed_tables


def single_type_id_downcast(table: Table) -> Table:
    """Downcast table with single geometry type.

    Downcast a table whose geometry column is known to contain (serialized) geometries
    of only a single type... to a table whose geometry column has a primitive GeoArrow
    type.
    """
    field_idx = get_geometry_column_index(table.schema)
    assert field_idx is not None, "Expected a geometry column in the table."
    orig_field = table.schema.field(field_idx)

    chunked_geo_arr = GeoChunkedArray.from_arrow(table.column(field_idx))
    downcasted_array = chunked_geo_arr.downcast(coord_type="interleaved")
    downcasted_field = Field.from_arrow(downcasted_array.type)
    assert is_primitive_geoarrow(downcasted_field), (
        "Inside of single_type_id_downcast, expected to be able to downcast to a single primitive GeoArrow type",
    )

    return table.set_column(
        field_idx,
        downcasted_field.with_name(orig_field.name),
        downcasted_array,
    )


def parse_geoparquet_table(table: Table) -> Table:
    """Parse GeoParquet table metadata, assigning it to GeoArrow metadata."""
    # If a column already has geoarrow metadata, don't parse from GeoParquet metadata
    if get_geometry_column_index(table.schema) is not None:
        return table

    schema_metadata = table.schema.metadata or {}
    geo_metadata_bytes = schema_metadata.get(b"geo")
    if not geo_metadata_bytes:
        return table

    try:
        geo_metadata = json.loads(geo_metadata_bytes)
    except json.JSONDecodeError:
        return table

    primary_column = geo_metadata["primary_column"]
    column_meta = geo_metadata["columns"][primary_column]
    column_idxes = [
        idx for idx, name in enumerate(table.column_names) if name == primary_column
    ]
    assert len(column_idxes) == 1, f"Expected one column with name {primary_column}"
    column_idx = column_idxes[0]
    if column_meta["encoding"] == "WKB":
        existing_field = table.schema.field(column_idx)
        existing_column = table.column(column_idx)
        crs_metadata = {"crs": column_meta.get("crs", OGC_84.to_json_dict())}
        metadata: dict[bytes, bytes] = {
            b"ARROW:extension:name": EXTENSION_NAME.WKB,
            b"ARROW:extension:metadata": json.dumps(crs_metadata).encode(),
        }
        new_field = existing_field.with_metadata(metadata)
        table = table.set_column(column_idx, new_field, existing_column)

    return table

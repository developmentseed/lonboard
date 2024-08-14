"""Handle GeoArrow tables with WKB-encoded geometry"""

import json
from typing import Dict, List

import numpy as np
from arro3.core import Array, Table

from lonboard._constants import EXTENSION_NAME, OGC_84
from lonboard._geoarrow.crs import get_field_crs
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._geoarrow.utils import is_native_geoarrow
from lonboard._utils import get_geometry_column_index


def parse_serialized_table(table: Table) -> List[Table]:
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

    extension_type_name = field.metadata.get(b"ARROW:extension:name")

    # For native GeoArrow input, return table as-is
    if is_native_geoarrow(extension_type_name):
        return [table]

    import shapely
    from shapely import GeometryType

    # Handle WKB/WKT input
    crs_str = get_field_crs(field)
    if extension_type_name in {EXTENSION_NAME.WKB, EXTENSION_NAME.OGC_WKB}:
        shapely_arr = shapely.from_wkb(column)
    elif extension_type_name == EXTENSION_NAME.WKT:
        shapely_arr = shapely.from_wkt(column)
    else:
        raise ValueError(f"Unexpected GeoArrow extension name {extension_type_name}")

    type_ids = np.array(shapely.get_type_id(shapely_arr))
    unique_type_ids = set(np.unique(type_ids))

    if GeometryType.GEOMETRYCOLLECTION in unique_type_ids:
        raise ValueError("GeometryCollections not currently supported")

    if GeometryType.LINEARRING in unique_type_ids:
        raise ValueError("LinearRings not currently supported")

    point_indices = np.where(
        (type_ids == GeometryType.POINT) | (type_ids == GeometryType.MULTIPOINT)
    )[0]

    linestring_indices = np.where(
        (type_ids == GeometryType.LINESTRING)
        | (type_ids == GeometryType.MULTILINESTRING)
    )[0]

    polygon_indices = np.where(
        (type_ids == GeometryType.POLYGON) | (type_ids == GeometryType.MULTIPOLYGON)
    )[0]

    # Here we intentionally check geometries in a specific order.
    # Starting from polygons, then linestrings, then points,
    # so that the order of generated layers is polygon, then path then scatterplot.
    # This ensures that points are rendered on top and polygons on the bottom.
    parsed_tables: List[Table] = []
    for single_type_geometry_indices in (
        polygon_indices,
        linestring_indices,
        point_indices,
    ):
        if len(single_type_geometry_indices) == 0:
            continue

        single_type_geometry_field, single_type_geometry_arr = construct_geometry_array(
            shapely_arr[single_type_geometry_indices],
            crs_str=crs_str,
        )

        concatted_table = table.combine_chunks()
        batches = concatted_table.to_batches()
        assert len(batches) == 1

        assert single_type_geometry_indices.dtype == np.int64
        single_type_geometry_indices_arrow = Array.from_numpy(
            single_type_geometry_indices
        )

        single_type_geometry_record_batch = (
            batches[0]
            .take(single_type_geometry_indices_arrow)
            .set_column(field_idx, single_type_geometry_field, single_type_geometry_arr)
        )
        parsed_tables.append(Table.from_batches([single_type_geometry_record_batch]))

    return parsed_tables


def parse_geoparquet_table(table: Table) -> Table:
    """Parse GeoParquet table metadata, assigning it to GeoArrow metadata"""
    # If a column already has geoarrow metadata, don't parse from GeoParquet metadata
    if get_geometry_column_index(table.schema) is not None:
        return table

    schema_metadata = table.schema.metadata or {}
    geo_metadata = schema_metadata.get(b"geo")
    if not geo_metadata:
        return table

    try:
        geo_metadata = json.loads(geo_metadata)
    except json.JSONDecodeError:
        return table

    primary_column = geo_metadata["primary_column"]
    column_meta = geo_metadata["columns"][primary_column]
    column_idx = [
        idx for idx, name in enumerate(table.column_names) if name == primary_column
    ]
    assert len(column_idx) == 1, f"Expected one column with name {primary_column}"
    column_idx = column_idx[0]
    if column_meta["encoding"] == "WKB":
        existing_field = table.schema.field(column_idx)
        existing_column = table.column(column_idx)
        crs_metadata = {"crs": column_meta.get("crs", OGC_84.to_json_dict())}
        metadata: Dict[bytes, bytes] = {
            b"ARROW:extension:name": EXTENSION_NAME.WKB,
            b"ARROW:extension:metadata": json.dumps(crs_metadata).encode(),
        }
        new_field = existing_field.with_metadata(metadata)
        table = table.set_column(column_idx, new_field, existing_column)

    return table

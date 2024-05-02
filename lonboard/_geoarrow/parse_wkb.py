"""Handle GeoArrow tables with WKB-encoded geometry"""

import json
from typing import List

import numpy as np
import pyarrow as pa
import shapely
import shapely.geometry
from shapely import GeometryType

from lonboard._constants import EXTENSION_NAME, OGC_84
from lonboard._geoarrow.crs import get_field_crs
from lonboard._geoarrow.extension_types import construct_geometry_array
from lonboard._utils import get_geometry_column_index


def parse_wkb_table(table: pa.Table) -> List[pa.Table]:
    """Parse a table with a WKB column into GeoArrow-native geometries.

    If no columns are WKB-encoded, returns the input. Note that WKB columns must be
    tagged with an extension name of `geoarrow.wkb` or `ogc.wkb`

    Returns one table per GeoArrow geometry type. E.g. if the input has points, lines,
    and polygons, then it returns three tables.
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
    if extension_type_name not in {EXTENSION_NAME.WKB, EXTENSION_NAME.OGC_WKB}:
        return [table]

    # Handle WKB input
    parsed_tables = []
    crs_str = get_field_crs(field)
    shapely_arr = shapely.from_wkb(column)

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

    if len(point_indices) > 0:
        point_field, point_arr = construct_geometry_array(
            shapely_arr[point_indices],
            crs_str=crs_str,
        )
        point_table = table.take(point_indices).set_column(
            field_idx, point_field, point_arr
        )
        parsed_tables.append(point_table)

    if len(linestring_indices) > 0:
        linestring_field, linestring_arr = construct_geometry_array(
            shapely_arr[linestring_indices],
            crs_str=crs_str,
        )
        linestring_table = table.take(linestring_indices).set_column(
            field_idx, linestring_field, linestring_arr
        )
        parsed_tables.append(linestring_table)

    if len(polygon_indices) > 0:
        polygon_field, polygon_arr = construct_geometry_array(
            shapely_arr[polygon_indices],
            crs_str=crs_str,
        )
        polygon_table = table.take(polygon_indices).set_column(
            field_idx, polygon_field, polygon_arr
        )
        parsed_tables.append(polygon_table)

    return parsed_tables


def parse_geoparquet_table(table: pa.Table) -> pa.Table:
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
        metadata = {
            b"ARROW:extension:name": EXTENSION_NAME.WKB,
            b"ARROW:extension:metadata": json.dumps(crs_metadata),
        }
        new_field = existing_field.with_metadata(metadata)
        table = table.set_column(column_idx, new_field, existing_column)

    return table

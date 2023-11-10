"""Helpers for viewport operations

This is partially derived from pydeck at
(https://github.com/visgl/deck.gl/blob/63728ecbdaa2f99811900ec3709e5df0f9f8d228/bindings/pydeck/pydeck/data_utils/viewport_helpers.py)
under the Apache 2 license.
"""

from __future__ import annotations

import math
from typing import List, Tuple

import pyarrow as pa

from lonboard._geoarrow.ops.bbox import Bbox, total_bounds
from lonboard._geoarrow.ops.centroid import WeightedCentroid, weighted_centroid
from lonboard._utils import get_geometry_column_index


def get_bbox_center(tables: List[pa.Table]) -> Tuple[Bbox, WeightedCentroid]:
    """Get the bounding box and geometric (weighted) center of the geometries in the
    table."""

    overall_bbox = Bbox()
    overall_centroid = WeightedCentroid()

    for table in tables:
        # Note: in the ArcLayer we won't necessarily have a column with a geoarrow
        # extension type/metadata
        try:
            geom_col_idx = get_geometry_column_index(table.schema)
        except ValueError:
            continue

        geom_field = table.schema.field(geom_col_idx)
        geom_col = table.column(geom_col_idx)

        table_bbox = total_bounds(geom_field, geom_col)
        overall_bbox.update(table_bbox)

        table_centroid = weighted_centroid(geom_field, geom_col)
        overall_centroid.update(table_centroid)

    return overall_bbox, overall_centroid


def bbox_to_zoom_level(bbox: Bbox) -> int:
    """Computes the zoom level of a bounding box

    This is copied from pydeck: https://github.com/visgl/deck.gl/blob/63728ecbdaa2f99811900ec3709e5df0f9f8d228/bindings/pydeck/pydeck/data_utils/viewport_helpers.py#L125C1-L149C22

    Returns:
        Zoom level of map in a WGS84 Mercator projection
    """
    lat_diff = max(bbox.miny, bbox.maxy) - min(bbox.miny, bbox.maxy)
    lng_diff = max(bbox.minx, bbox.maxx) - min(bbox.minx, bbox.maxx)

    max_diff = max(lng_diff, lat_diff)
    zoom_level = None
    if max_diff < (360.0 / math.pow(2, 20)):
        zoom_level = 21
    else:
        zoom_level = int(
            -1
            * ((math.log(max_diff) / math.log(2.0)) - (math.log(360.0) / math.log(2)))
        )
        if zoom_level < 1:
            zoom_level = 1

    return zoom_level


def compute_view(tables: List[pa.Table]):
    """Automatically computes a view state for the data passed in."""
    bbox, center = get_bbox_center(tables)
    # When no geo column is found, bbox will have inf values
    try:
        zoom = bbox_to_zoom_level(bbox)
        return {"longitude": center.x, "latitude": center.y, "zoom": zoom}
    except OverflowError:
        return {"longitude": center.x or 0, "latitude": center.y or 0, "zoom": 0}

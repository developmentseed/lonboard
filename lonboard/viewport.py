"""Helpers for viewport operations

This is partially derived from pydeck at
(https://github.com/visgl/deck.gl/blob/63728ecbdaa2f99811900ec3709e5df0f9f8d228/bindings/pydeck/pydeck/data_utils/viewport_helpers.py)
under the Apache 2 license.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pyarrow as pa

from lonboard.utils import get_geometry_column_index


@dataclass
class Bbox:
    minx: float = math.inf
    miny: float = math.inf
    maxx: float = -math.inf
    maxy: float = -math.inf

    def update(self, other: Bbox):
        if other.minx < self.minx:
            self.minx = other.minx
        if other.miny < self.miny:
            self.miny = other.miny
        if other.maxx > self.maxx:
            self.maxx = other.maxx
        if other.maxy > self.maxy:
            self.maxy = other.maxy

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.minx, self.miny, self.maxx, self.maxy)


def geo_mean_overflow(iterable):
    return np.exp(np.log(iterable).mean())


def geo_mean(iterable):
    a = np.array(iterable)
    return a.prod() ** (1.0 / len(a))


@dataclass
class WeightedCentroid:
    # Existing average for x and y
    x: Optional[float] = None
    y: Optional[float] = None
    num_items: int = 0

    def update(self, coords: pa.FixedSizeListArray):
        """Update the average for x and y based on a new chunk of data

        Note that this does not keep a cumulative sum due to precision concerns. Rather
        it incrementally updates based on a delta, and never multiplies to large
        constant values.

        Note: this currently computes the mean weighted _per coordinate_ and not _per
        geometry_.
        """
        np_arr = coords.flatten().to_numpy().reshape(-1, coords.type.list_size)
        new_chunk_len = np_arr.shape[0]

        if self.x is None or self.y is None:
            assert self.x is None and self.y is None and self.num_items == 0
            self.x = np.mean(np_arr[:, 0])
            self.y = np.mean(np_arr[:, 1])
            self.num_items = new_chunk_len
            return

        existing_modifier = self.num_items / (self.num_items + new_chunk_len)
        new_chunk_modifier = new_chunk_len / (self.num_items + new_chunk_len)

        new_chunk_avg_x = np.mean(np_arr[:, 0])
        new_chunk_avg_y = np.mean(np_arr[:, 0])

        existing_x_avg = self.x
        existing_y_avg = self.y

        self.x = (
            existing_x_avg * existing_modifier + new_chunk_avg_x * new_chunk_modifier
        )
        self.y = (
            existing_y_avg * existing_modifier + new_chunk_avg_y * new_chunk_modifier
        )
        self.num_items += new_chunk_len


def get_bbox_center(table: pa.Table) -> Tuple[Bbox, WeightedCentroid]:
    """Get the bounding box and geometric (weighted) center of the geometries in the
    table."""
    geom_col_idx = get_geometry_column_index(table.schema)
    geom_col = table.column(geom_col_idx)
    extension_type_name = table.schema.field(geom_col_idx).metadata[
        b"ARROW:extension:name"
    ]

    if extension_type_name == b"geoarrow.point":
        return _get_bbox_center_nest_0(geom_col)

    if extension_type_name in [b"geoarrow.linestring", b"geoarrow.multipoint"]:
        return _get_bbox_center_nest_1(geom_col)

    if extension_type_name in [b"geoarrow.polygon", b"geoarrow.multilinestring"]:
        return _get_bbox_center_nest_2(geom_col)

    if extension_type_name == b"geoarrow.multipolygon":
        return _get_bbox_center_nest_3(geom_col)

    assert False


def _coords_bbox(arr: pa.FixedSizeListArray) -> Bbox:
    np_arr = arr.flatten().to_numpy().reshape(-1, arr.type.list_size)
    min_vals = np.min(np_arr, axis=0)
    max_vals = np.max(np_arr, axis=0)
    return Bbox(minx=min_vals[0], miny=min_vals[1], maxx=max_vals[0], maxy=max_vals[1])


def _get_bbox_center_nest_0(column: pa.ChunkedArray) -> Tuple[Bbox, WeightedCentroid]:
    bbox = Bbox()
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk
        bbox.update(_coords_bbox(coords))
        centroid.update(coords)

    return (bbox, centroid)


def _get_bbox_center_nest_1(column: pa.ChunkedArray) -> Tuple[Bbox, WeightedCentroid]:
    bbox = Bbox()
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten()
        bbox.update(_coords_bbox(coords))
        centroid.update(coords)

    return (bbox, centroid)


def _get_bbox_center_nest_2(column: pa.ChunkedArray) -> Tuple[Bbox, WeightedCentroid]:
    bbox = Bbox()
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten().flatten()
        bbox.update(_coords_bbox(coords))
        centroid.update(coords)

    return (bbox, centroid)


def _get_bbox_center_nest_3(column: pa.ChunkedArray) -> Tuple[Bbox, WeightedCentroid]:
    bbox = Bbox()
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten().flatten().flatten()
        bbox.update(_coords_bbox(coords))
        centroid.update(coords)

    return (bbox, centroid)


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


def compute_view(table: pa.Table):
    """Automatically computes a view state for the data passed in."""
    bbox, center = get_bbox_center(table)
    zoom = bbox_to_zoom_level(bbox)
    return {"longitude": center.x, "latitude": center.y, "zoom": zoom}

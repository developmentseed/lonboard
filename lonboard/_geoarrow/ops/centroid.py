"""Compute the weighted centroid of geometries
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pyarrow as pa

from lonboard._constants import EXTENSION_NAME


@dataclass
class WeightedCentroid:
    # Existing average for x and y
    x: Optional[float] = None
    y: Optional[float] = None
    num_items: int = 0

    def update(self, other: WeightedCentroid):
        new_chunk_len = other.num_items

        if self.x is None or self.y is None:
            assert self.x is None and self.y is None and self.num_items == 0
            self.x = other.x
            self.y = other.y
            self.num_items = new_chunk_len
            return

        if other.x is None or other.y is None or other.num_items == 0:
            # Can't update from an uninitialized centroid
            return

        existing_modifier = self.num_items / (self.num_items + new_chunk_len)
        new_chunk_modifier = new_chunk_len / (self.num_items + new_chunk_len)

        new_chunk_avg_x = other.x
        new_chunk_avg_y = other.y

        existing_x_avg = self.x
        existing_y_avg = self.y

        self.x = (
            existing_x_avg * existing_modifier + new_chunk_avg_x * new_chunk_modifier
        )
        self.y = (
            existing_y_avg * existing_modifier + new_chunk_avg_y * new_chunk_modifier
        )
        self.num_items += new_chunk_len

    def update_coords(self, coords: pa.FixedSizeListArray):
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


def weighted_centroid(field: pa.Field, column: pa.ChunkedArray) -> WeightedCentroid:
    """Get the bounding box and geometric (weighted) center of the geometries in the
    table."""
    extension_type_name = field.metadata[b"ARROW:extension:name"]

    if extension_type_name == EXTENSION_NAME.POINT:
        return _weighted_centroid_nest_0(column)

    if extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        return _weighted_centroid_nest_1(column)

    if extension_type_name in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTILINESTRING]:
        return _weighted_centroid_nest_2(column)

    if extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        return _weighted_centroid_nest_3(column)

    assert False


def _weighted_centroid_nest_0(column: pa.ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_1(column: pa.ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten()
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_2(column: pa.ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten().flatten()
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_3(column: pa.ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk.flatten().flatten().flatten()
        centroid.update_coords(coords)

    return centroid

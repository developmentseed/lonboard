"""Compute the weighted centroid of geometries."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, Field, list_flatten, struct_field

from lonboard._constants import EXTENSION_NAME


@dataclass
class WeightedCentroid:
    # Existing average for x and y
    x: float | None = None
    y: float | None = None
    num_items: int = 0

    def update(self, other: WeightedCentroid) -> None:
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

    def update_coords(self, coords: Array) -> None:
        """Update the average for x and y based on a new chunk of data.

        Note that this does not keep a cumulative sum due to precision concerns. Rather
        it incrementally updates based on a delta, and never multiplies to large
        constant values.

        Note: this currently computes the mean weighted _per coordinate_ and not _per
        geometry_.
        """
        assert DataType.is_fixed_size_list(coords.type)
        list_size = coords.type.list_size
        assert list_size is not None

        np_arr = list_flatten(coords).to_numpy().reshape(-1, list_size)
        new_chunk_len = np_arr.shape[0]

        if self.x is None or self.y is None:
            assert self.x is None and self.y is None and self.num_items == 0
            self.x = float(np.mean(np_arr[:, 0]))
            self.y = float(np.mean(np_arr[:, 1]))
            self.num_items = new_chunk_len
            return

        existing_modifier = self.num_items / (self.num_items + new_chunk_len)
        new_chunk_modifier = new_chunk_len / (self.num_items + new_chunk_len)

        new_chunk_avg_x = np.mean(np_arr[:, 0])
        new_chunk_avg_y = np.mean(np_arr[:, 1])

        existing_x_avg = self.x
        existing_y_avg = self.y

        self.x = float(
            existing_x_avg * existing_modifier + new_chunk_avg_x * new_chunk_modifier,
        )
        self.y = float(
            existing_y_avg * existing_modifier + new_chunk_avg_y * new_chunk_modifier,
        )
        self.num_items += new_chunk_len


def weighted_centroid(field: Field, column: ChunkedArray) -> WeightedCentroid:
    """Get the bounding box and geometric (weighted) center.

    Of all geometries in the table.
    """
    extension_type_name = field.metadata[b"ARROW:extension:name"]

    if extension_type_name == EXTENSION_NAME.POINT:
        return _weighted_centroid_nest_0(column)

    if extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        return _weighted_centroid_nest_1(column)

    if extension_type_name in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTILINESTRING]:
        return _weighted_centroid_nest_2(column)

    if extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        return _weighted_centroid_nest_3(column)

    if extension_type_name == EXTENSION_NAME.BOX:
        return _weighted_centroid_box(column)

    assert False


def _weighted_centroid_nest_0(column: ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        coords = chunk
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_1(column: ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    flat_array = list_flatten(column)
    for coords in flat_array:
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_2(column: ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    flat_array = list_flatten(list_flatten(column))
    for coords in flat_array:
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_nest_3(column: ChunkedArray) -> WeightedCentroid:
    centroid = WeightedCentroid()
    flat_array = list_flatten(list_flatten(list_flatten(column)))
    for coords in flat_array:
        centroid.update_coords(coords)

    return centroid


def _weighted_centroid_box(column: ChunkedArray) -> WeightedCentroid:
    """Compute the weighted centroid of a box geometry."""
    centroid = WeightedCentroid()
    for chunk in column.chunks:
        is_2d = len(chunk.field.type.fields) == 4
        is_3d = len(chunk.field.type.fields) == 6

        if is_2d:
            minx = struct_field(chunk, 0)
            miny = struct_field(chunk, 1)
            maxx = struct_field(chunk, 2)
            maxy = struct_field(chunk, 3)
        elif is_3d:
            minx = struct_field(chunk, 0)
            miny = struct_field(chunk, 1)
            maxx = struct_field(chunk, 3)
            maxy = struct_field(chunk, 4)
        else:
            raise ValueError(
                f"Unexpected box type with {len(chunk.field.type.fields)} fields.\n"
                "Only 2D and 3D boxes are supported.",
            )

        meanx = float((np.mean(minx) + np.mean(maxx)) / 2)
        meany = float((np.mean(miny) + np.mean(maxy)) / 2)

        centroid.update(WeightedCentroid(x=meanx, y=meany, num_items=len(chunk)))

    return centroid

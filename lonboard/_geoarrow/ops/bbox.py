"""Compute the total bounds of a geoarrow column."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, Field, list_flatten, struct_field

from lonboard._constants import EXTENSION_NAME


@dataclass
class Bbox:
    minx: float = math.inf
    miny: float = math.inf
    maxx: float = -math.inf
    maxy: float = -math.inf

    def update(self, other: Bbox) -> None:
        self.minx = min(self.minx, other.minx)
        self.miny = min(self.miny, other.miny)
        self.maxx = max(self.maxx, other.maxx)
        self.maxy = max(self.maxy, other.maxy)

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.minx, self.miny, self.maxx, self.maxy)


def total_bounds(field: Field, column: ChunkedArray) -> Bbox:
    """Compute the total bounds of a geometry column."""
    extension_type_name = field.metadata[b"ARROW:extension:name"]

    if extension_type_name == EXTENSION_NAME.POINT:
        return _total_bounds_nest_0(column)

    if extension_type_name in [EXTENSION_NAME.LINESTRING, EXTENSION_NAME.MULTIPOINT]:
        return _total_bounds_nest_1(column)

    if extension_type_name in [EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTILINESTRING]:
        return _total_bounds_nest_2(column)

    if extension_type_name == EXTENSION_NAME.MULTIPOLYGON:
        return _total_bounds_nest_3(column)

    if extension_type_name == EXTENSION_NAME.BOX:
        return _total_bounds_box(column)

    assert False


def _coords_bbox(arr: Array) -> Bbox:
    assert DataType.is_fixed_size_list(arr.type)
    list_size = arr.type.list_size
    assert list_size is not None

    np_arr = list_flatten(arr).to_numpy().reshape(-1, list_size)
    min_vals = np.min(np_arr, axis=0)
    max_vals = np.max(np_arr, axis=0)
    return Bbox(minx=min_vals[0], miny=min_vals[1], maxx=max_vals[0], maxy=max_vals[1])


def _total_bounds_nest_0(column: ChunkedArray) -> Bbox:
    bbox = Bbox()
    for coords in column.chunks:
        bbox.update(_coords_bbox(coords))

    return bbox


def _total_bounds_nest_1(column: ChunkedArray) -> Bbox:
    bbox = Bbox()
    flat_array = list_flatten(column)
    for coords in flat_array:
        bbox.update(_coords_bbox(coords))

    return bbox


def _total_bounds_nest_2(column: ChunkedArray) -> Bbox:
    bbox = Bbox()
    flat_array = list_flatten(list_flatten(column))
    for coords in flat_array:
        bbox.update(_coords_bbox(coords))

    return bbox


def _total_bounds_nest_3(column: ChunkedArray) -> Bbox:
    bbox = Bbox()
    flat_array = list_flatten(list_flatten(list_flatten(column)))
    for coords in flat_array:
        bbox.update(_coords_bbox(coords))

    return bbox


def _total_bounds_box(column: ChunkedArray) -> Bbox:
    """Compute the total bounds of a geoarrow.box column."""
    bbox = Bbox()
    for chunk in column.chunks:
        is_2d = len(chunk.field.type.fields) == 4
        is_3d = len(chunk.field.type.fields) == 6

        if is_2d:
            minx = np.min(struct_field(chunk, 0))
            miny = np.min(struct_field(chunk, 1))
            maxx = np.max(struct_field(chunk, 2))
            maxy = np.max(struct_field(chunk, 3))
        elif is_3d:
            minx = np.min(struct_field(chunk, 0))
            miny = np.min(struct_field(chunk, 1))
            maxx = np.max(struct_field(chunk, 3))
            maxy = np.max(struct_field(chunk, 4))
        else:
            raise ValueError(
                f"Unexpected box type with {len(chunk.field.type.fields)} fields.\n"
                "Only 2D and 3D boxes are supported.",
            )
        bbox.update(Bbox(minx=minx, miny=miny, maxx=maxx, maxy=maxy))

    return bbox

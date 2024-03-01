from __future__ import annotations

import sys
from typing import (
    List,
    Literal,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

import numpy as np
import pandas as pd
import pyarrow as pa
from numpy.typing import NDArray

from lonboard._base import BaseExtension

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class ArrowArrayExportable(Protocol):
    def __arrow_c_array__(
        self, requested_schema: object | None = None
    ) -> Tuple[object, object]:
        ...


IntFloat = Union[int, float]
Units = Literal["meters", "common", "pixels"]

ColorAccessorInput = Union[
    List[int],
    Tuple[int, int, int],
    Tuple[int, ...],
    str,
    NDArray[np.uint8],
    pa.FixedSizeListArray,
    pa.ChunkedArray,
    ArrowArrayExportable,
]
FloatAccessorInput = Union[
    int,
    float,
    NDArray[np.number],
    pd.Series,
    pa.FloatingPointArray,
    pa.ChunkedArray,
    ArrowArrayExportable,
]
NormalAccessorInput = Union[
    List[int],
    Tuple[int, int, int],
    Tuple[int, ...],
    NDArray[np.floating],
    pa.FixedSizeListArray,
    pa.ChunkedArray,
    ArrowArrayExportable,
]
TextAccessorInput = Union[
    str,
    NDArray[np.str_],
    pd.Series,
    pa.StringArray,
    pa.LargeStringArray,
    pa.ChunkedArray,
    ArrowArrayExportable,
]


class BaseLayerKwargs(TypedDict, total=False):
    extensions: Sequence[BaseExtension]
    pickable: bool
    visible: bool
    opacity: IntFloat
    auto_highlight: bool


class BitmapLayerKwargs(BaseLayerKwargs, total=False):
    image: str
    bounds: Union[
        Tuple[IntFloat, IntFloat, IntFloat, IntFloat],
        Tuple[
            Tuple[IntFloat, IntFloat],
            Tuple[IntFloat, IntFloat],
            Tuple[IntFloat, IntFloat],
            Tuple[IntFloat, IntFloat],
        ],
    ]
    desaturate: IntFloat
    transparent_color: Sequence[IntFloat]
    tint_color: Sequence[IntFloat]


class BitmapTileLayerKwargs(BaseLayerKwargs, total=False):
    data: Union[str, Sequence[str]]
    tile_size: int
    zoom_offset: int
    max_zoom: int
    min_zoom: int
    extent: Sequence[IntFloat]
    max_cache_size: int
    # max_cache_byte_size: int
    refinement_strategy: Literal["best-available", "no-overlap", "never"]
    max_requests: int
    desaturate: IntFloat
    transparent_color: Sequence[IntFloat]
    tint_color: Sequence[IntFloat]


class PathLayerKwargs(BaseLayerKwargs, total=False):
    width_units: Units
    width_scale: IntFloat
    width_min_pixels: IntFloat
    width_max_pixels: IntFloat
    joint_rounded: bool
    cap_rounded: bool
    miter_limit: int
    billboard: bool
    get_color: ColorAccessorInput
    get_width: FloatAccessorInput


class PointCloudLayerKwargs(BaseLayerKwargs, total=False):
    size_units: Units
    point_size: IntFloat
    get_color: ColorAccessorInput
    get_normal: NormalAccessorInput


class ScatterplotLayerKwargs(BaseLayerKwargs, total=False):
    radius_units: Units
    radius_scale: IntFloat
    radius_min_pixels: IntFloat
    radius_max_pixels: IntFloat
    line_width_units: Units
    line_width_scale: IntFloat
    line_width_min_pixels: IntFloat
    line_width_max_pixels: IntFloat
    stroked: bool
    filled: bool
    billboard: bool
    antialiasing: bool
    get_radius: FloatAccessorInput
    get_fill_color: ColorAccessorInput
    get_line_color: ColorAccessorInput
    get_line_width: FloatAccessorInput


class SolidPolygonLayerKwargs(BaseLayerKwargs, total=False):
    filled: bool
    extruded: bool
    wireframe: bool
    elevation_scale: IntFloat
    get_elevation: FloatAccessorInput
    get_fill_color: ColorAccessorInput
    get_line_color: ColorAccessorInput


class HeatmapLayerKwargs(BaseLayerKwargs, total=False):
    radius_pixels: IntFloat
    intensity: IntFloat
    threshold: IntFloat
    color_domain: Tuple[IntFloat, IntFloat]
    aggregation: Literal["SUM", "MEAN"]
    weights_texture_size: int
    debounce_timeout: int
    get_weight: FloatAccessorInput

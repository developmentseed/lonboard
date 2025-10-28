# Notes:
#
# - See module docstring of lonboard.layer for note on passing None as default value.

# ruff: noqa

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import ipywidgets
import traitlets
import traitlets as t
from arro3.core import DataType, Scalar

from lonboard._constants import EXTENSION_NAME, MIN_INTEGER_FLOAT32
from lonboard.layer._base import BaseArrowLayer
from lonboard._utils import timestamp_max_physical_value, timestamp_start_offset
from lonboard.traits import (
    TimestampAccessor,
    ArrowTableTrait,
    ColorAccessor,
    FloatAccessor,
    PointAccessor,
    TextAccessor,
)
from lonboard.types.layer import ArcLayerKwargs, PointAccessorInput

if TYPE_CHECKING:
    import sys

    import duckdb
    import geopandas as gpd
    import pyproj
    from arro3.core.types import ArrowStreamExportable
    from movingpandas import TrajectoryCollection

    from lonboard.types.layer import TripsLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class TextLayer(BaseArrowLayer):
    """Render text labels at given coordinates."""

    _layer_type = t.Unicode("text").tag(sync=True)

    table = ArrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    billboard = t.Bool(None, allow_none=True).tag(sync=True)
    """If `true`, the text always faces camera. Otherwise the text faces up (z).

    - Type: `bool`
    - Default: `True`
    """

    size_scale = t.Any(None, allow_none=True).tag(sync=True)
    """Text size multiplier.

    - Type: `float`.
    - Default: `1`
    """

    size_units = t.Any(None, allow_none=True).tag(sync=True)
    """The units of the size, one of `'meters'`, `'common'`, and `'pixels'`.
    default 'pixels'. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    size_min_pixels = t.Any(None, allow_none=True).tag(sync=True)
    """
    The minimum size in pixels. When using non-pixel `sizeUnits`, this prop can be used
    to prevent the icon from getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    size_max_pixels = t.Any(None, allow_none=True).tag(sync=True)
    """
    The maximum size in pixels. When using non-pixel `sizeUnits`, this prop can be used
    to prevent the icon from getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    # background = t.Bool(None, allow_none=True).tag(sync=True)
    # """Whether to render background for the text blocks.

    # - Type: `bool`
    # - Default: `False`
    # """

    get_background_color = ColorAccessor(None, allow_none=True)
    """Background color accessor.

    default [255, 255, 255, 255]
    """

    get_border_color = ColorAccessor(None, allow_none=True)
    """Border color accessor.

    default [0, 0, 0, 255]
    """

    get_border_width = FloatAccessor(None, allow_none=True)
    """Border width accessor.

    default 0
    """

    background_padding = t.Any(None, allow_none=True).tag(sync=True)
    """The padding of the background.

    - If an array of 2 is supplied, it is interpreted as `[padding_x, padding_y]` in
      pixels.
    - If an array of 4 is supplied, it is interpreted as `[padding_left, padding_top,
      padding_right, padding_bottom]` in pixels.

    default [0, 0, 0, 0]
    """

    character_set = t.Any(None, allow_none=True).tag(sync=True)
    """
    Specifies a list of characters to include in the font. If set to 'auto', will be
    automatically generated from the data set.

    default (ASCII characters 32-128)
    """

    font_family = t.Any(None, allow_none=True).tag(sync=True)
    """CSS font family

    default 'Monaco, monospace'
    """

    font_weight = t.Any(None, allow_none=True).tag(sync=True)
    """CSS font weight

    default 'normal'
    """

    line_height = t.Any(None, allow_none=True).tag(sync=True)
    """
    A unitless number that will be multiplied with the current text size to set the line
    height.
    """

    outline_width = t.Any(None, allow_none=True).tag(sync=True)
    """
    Width of outline around the text, relative to the text size. Only effective if
    `fontSettings.sdf` is `true`.

    default 0
    """

    outline_color = t.Any(None, allow_none=True).tag(sync=True)
    """
    Color of outline around the text, in `[r, g, b, [a]]`. Each channel is a number
    between 0-255 and `a` is 255 if not supplied.

    default [0, 0, 0, 255]
    """

    font_settings = t.Any(None, allow_none=True).tag(sync=True)
    """
    Advance options for fine tuning the appearance and performance of the generated
    shared `fontAtlas`.
    """

    word_break = t.Any(None, allow_none=True).tag(sync=True)
    """
    Available options are `break-all` and `break-word`. A valid `maxWidth` has to be
    provided to use `wordBreak`.

    default 'break-word'
    """

    max_width = t.Any(None, allow_none=True).tag(sync=True)
    """
    A unitless number that will be multiplied with the current text size to set the
    width limit of a string.

    If specified, when the text is longer than the width limit, it will be wrapped into
    multiple lines using the strategy of `wordBreak`.

    default -1
    """

    get_text = TextAccessor(None, allow_none=True)
    """Label text accessor"""

    # get_position = t.Any(None, allow_none=True).tag(sync=True)
    # """Anchor position accessor"""

    #  ?: Accessor<DataT, Position>;

    get_color = ColorAccessor(None, allow_none=True)
    """Label color accessor

    default [0, 0, 0, 255]
    """

    get_size = FloatAccessor(None, allow_none=True)
    """Label size accessor

    default 32
    """

    get_angle = FloatAccessor(None, allow_none=True)
    """Label rotation accessor, in degrees

    default 0
    """

    get_text_anchor = t.Any(None, allow_none=True).tag(sync=True)
    """Horizontal alignment accessor

    default 'middle'
    """
    #  ?: Accessor<DataT, 'start' | 'middle' | 'end'>;

    get_alignment_baseline = t.Any(None, allow_none=True).tag(sync=True)
    """Vertical alignment accessor

    default 'center'
    """
    #  ?: Accessor<DataT, 'top' | 'center' | 'bottom'>;

    get_pixel_offset = t.Any(None, allow_none=True).tag(sync=True)
    """Label offset from the anchor position, [x, y] in pixels

    default [0, 0]
    """
    #  ?: Accessor<DataT, [number, number]>;

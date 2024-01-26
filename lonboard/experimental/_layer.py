"""Notes:

- See module docstring of lonboard._layer for note on passing None as default value.
"""

from __future__ import annotations

import traitlets

from lonboard._constants import EXTENSION_NAME
from lonboard._layer import BaseArrowLayer
from lonboard.experimental.traits import PointAccessor
from lonboard.traits import (
    ColorAccessor,
    FloatAccessor,
    PyarrowTableTrait,
    TextAccessor,
)


class ArcLayer(BaseArrowLayer):
    """Render raised arcs joining pairs of source and target coordinates."""

    _layer_type = traitlets.Unicode("arc").tag(sync=True)

    table = PyarrowTableTrait()
    """A GeoArrow table.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    great_circle = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """If `True`, create the arc along the shortest path on the earth surface.

    - Type: `bool`, optional
    - Default: `False`
    """

    num_segments = traitlets.Int(None, allow_none=True).tag(sync=True)
    """The number of segments used to draw each arc.

    - Type: `int`, optional
    - Default: `50`
    """

    width_units = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    width_scale = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The scaling multiplier for the width of each line.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """The minimum line width in pixels.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = traitlets.Float(None, allow_none=True, min=0).tag(sync=True)
    """The maximum line width in pixels.

    - Type: `float`, optional
    - Default: `None`
    """

    get_source_position = PointAccessor()
    """Source position of each object
    """

    get_target_position = PointAccessor()
    """Target position of each object
    """

    get_source_color = ColorAccessor()
    """Source color of each object
    """

    get_target_color = ColorAccessor()
    """Target color of each object
    """

    get_width = FloatAccessor()
    """The line width of each object, in units specified by `widthUnits`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """

    get_height = FloatAccessor()
    """Height color of each object
    """

    get_tilt = FloatAccessor()
    """
    Use to tilt the arc to the side if you have multiple arcs with the same source and
    target positions.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `0`.
    """


class TextLayer(BaseArrowLayer):
    """Render text labels at given coordinates."""

    _layer_type = traitlets.Unicode("text").tag(sync=True)

    table = PyarrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    billboard = traitlets.Bool(None, allow_none=True).tag(sync=True)
    """If `true`, the text always faces camera. Otherwise the text faces up (z).

    - Type: `bool`
    - Default: `True`
    """

    size_scale = traitlets.Any(None, allow_none=True).tag(sync=True)
    """Text size multiplier.

    - Type: `float`.
    - Default: `1`
    """

    size_units = traitlets.Any(None, allow_none=True).tag(sync=True)
    """The units of the size, one of `'meters'`, `'common'`, and `'pixels'`.
    default 'pixels'. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    size_min_pixels = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    The minimum size in pixels. When using non-pixel `sizeUnits`, this prop can be used
    to prevent the icon from getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    size_max_pixels = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    The maximum size in pixels. When using non-pixel `sizeUnits`, this prop can be used
    to prevent the icon from getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    # background = traitlets.Bool(None, allow_none=True).tag(sync=True)
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

    background_padding = traitlets.Any(None, allow_none=True).tag(sync=True)
    """The padding of the background.

    - If an array of 2 is supplied, it is interpreted as `[padding_x, padding_y]` in
      pixels.
    - If an array of 4 is supplied, it is interpreted as `[padding_left, padding_top,
      padding_right, padding_bottom]` in pixels.

    default [0, 0, 0, 0]
    """

    character_set = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    Specifies a list of characters to include in the font. If set to 'auto', will be
    automatically generated from the data set.

    default (ASCII characters 32-128)
    """

    font_family = traitlets.Any(None, allow_none=True).tag(sync=True)
    """CSS font family

    default 'Monaco, monospace'
    """

    font_weight = traitlets.Any(None, allow_none=True).tag(sync=True)
    """CSS font weight

    default 'normal'
    """

    line_height = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    A unitless number that will be multiplied with the current text size to set the line
    height.
    """

    outline_width = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    Width of outline around the text, relative to the text size. Only effective if
    `fontSettings.sdf` is `true`.

    default 0
    """

    outline_color = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    Color of outline around the text, in `[r, g, b, [a]]`. Each channel is a number
    between 0-255 and `a` is 255 if not supplied.

    default [0, 0, 0, 255]
    """

    font_settings = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    Advance options for fine tuning the appearance and performance of the generated
    shared `fontAtlas`.
    """

    word_break = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    Available options are `break-all` and `break-word`. A valid `maxWidth` has to be
    provided to use `wordBreak`.

    default 'break-word'
    """

    max_width = traitlets.Any(None, allow_none=True).tag(sync=True)
    """
    A unitless number that will be multiplied with the current text size to set the
    width limit of a string.

    If specified, when the text is longer than the width limit, it will be wrapped into
    multiple lines using the strategy of `wordBreak`.

    default -1
    """

    get_text = TextAccessor(None, allow_none=True)
    """Label text accessor"""

    # get_position = traitlets.Any(None, allow_none=True).tag(sync=True)
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

    get_text_anchor = traitlets.Any(None, allow_none=True).tag(sync=True)
    """Horizontal alignment accessor

    default 'middle'
    """
    #  ?: Accessor<DataT, 'start' | 'middle' | 'end'>;

    get_alignment_baseline = traitlets.Any(None, allow_none=True).tag(sync=True)
    """Vertical alignment accessor

    default 'center'
    """
    #  ?: Accessor<DataT, 'top' | 'center' | 'bottom'>;

    get_pixel_offset = traitlets.Any(None, allow_none=True).tag(sync=True)
    """Label offset from the anchor position, [x, y] in pixels

    default [0, 0]
    """
    #  ?: Accessor<DataT, [number, number]>;

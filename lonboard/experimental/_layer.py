# Notes:
#
# - See module docstring of lonboard._layer for note on passing None as default value.

# ruff: noqa

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import ipywidgets
import traitlets
import traitlets as t
from arro3.core import DataType, Scalar

from lonboard._constants import EXTENSION_NAME, MIN_INTEGER_FLOAT32
from lonboard._layer import BaseArrowLayer
from lonboard._utils import timestamp_max_physical_value, timestamp_start_offset
from lonboard.experimental.traits import TimestampAccessor
from lonboard.traits import (
    ArrowTableTrait,
    ColorAccessor,
    FloatAccessor,
    PointAccessor,
    TextAccessor,
)

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


class ArcLayer(BaseArrowLayer):
    """Render raised arcs joining pairs of source and target coordinates."""

    _layer_type = t.Unicode("arc").tag(sync=True)

    table = ArrowTableTrait(geometry_required=False)
    """A GeoArrow table.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    great_circle = t.Bool(None, allow_none=True).tag(sync=True)
    """If `True`, create the arc along the shortest path on the earth surface.

    - Type: `bool`, optional
    - Default: `False`
    """

    num_segments = t.Int(None, allow_none=True).tag(sync=True)
    """The number of segments used to draw each arc.

    - Type: `int`, optional
    - Default: `50`
    """

    width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The scaling multiplier for the width of each line.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The minimum line width in pixels.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The maximum line width in pixels.

    - Type: `float`, optional
    - Default: `None`
    """

    get_source_position = PointAccessor(None, allow_none=True)
    """Source position of each object
    """

    get_target_position = PointAccessor(None, allow_none=True)
    """Target position of each object
    """

    get_source_color = ColorAccessor(None, allow_none=True)
    """Source color of each object
    """

    get_target_color = ColorAccessor(None, allow_none=True)
    """Target color of each object
    """

    get_width = FloatAccessor(None, allow_none=True)
    """The line width of each object, in units specified by `widthUnits`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """

    get_height = FloatAccessor(None, allow_none=True)
    """Height color of each object
    """

    get_tilt = FloatAccessor(None, allow_none=True)
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


class TripsLayer(BaseArrowLayer):
    """The `TripsLayer` renders animated paths that represent moving objects.

    The easiest way to create a `TripsLayer` is by using the
    [`from_movingpandas`][lonboard.experimental.TripsLayer.from_movingpandas]
    constructor, where you can pass in a [`movingpandas.TrajectoryCollection`][].

    Otherwise, this layer requires a specific Arrow input data schema to associate the
    timestamp of each coordinate with the spatial information in the `LineString`
    geometries.

    In order to animate this layer, call the
    [`animate`][lonboard.experimental.TripsLayer.animate] method.

    !!! warning

        The TripsLayer renders data representing a specific instance in time based on
        the [`current_time`][lonboard.experimental.TripsLayer.current_time] attribute.

        If you don't see any data, use the
        [`animate`][lonboard.experimental.TripsLayer.animate] method to automatically
        set `current_time`.

    !!! info "Passing in custom Arrow data"

        As with all layers, you can pass an Arrow `Table` into the `table` parameter of
        this layer. In the case of the `TripsLayer`, there must be one column in the
        table that is a GeoArrow `LineString` geometry column, tagged with the
        `geoarrow.linestring` extension name. Additionally, the
        [`get_timestamps`][lonboard.experimental.TripsLayer.get_timestamps] accessor
        needs to be an Arrow list-typed column with a timestamp-typed child array. The
        `get_timestamps` column must have the **exact same nesting** as the `LineString`
        column. That is, there must be one timestamp for every coordinate in the
        `LineString` column. This is validated in data input.
    """

    _animation_link: ipywidgets.widgets.widget_link.DirectionalLink | None = None
    """
    An ipywidgets link created and managed by `animate`. A reference is stored here so
    that we can call `unlink` on the previous link object if `animate` is called
    multiple times.
    """

    _layer_type = traitlets.Unicode("trip").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={
            EXTENSION_NAME.LINESTRING,
        },
    )

    width_units = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    width_scale = traitlets.Float(default_value=None, allow_none=True, min=0).tag(
        sync=True,
    )
    """
    The path width multiplier that multiplied to all paths.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = traitlets.Float(default_value=None, allow_none=True, min=0).tag(
        sync=True,
    )
    """
    The minimum path width in pixels. This prop can be used to prevent the path from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = traitlets.Float(default_value=None, allow_none=True, min=0).tag(
        sync=True,
    )
    """
    The maximum path width in pixels. This prop can be used to prevent the path from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    joint_rounded = traitlets.Bool(default_value=None, allow_none=True).tag(sync=True)
    """
    Type of joint. If `True`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    cap_rounded = traitlets.Bool(default_value=None, allow_none=True).tag(sync=True)
    """
    Type of caps. If `True`, draw round caps. Otherwise draw square caps.

    - Type: `bool`, optional
    - Default: `False`
    """

    miter_limit = traitlets.Int(default_value=None, allow_none=True).tag(sync=True)
    """
    The maximum extent of a joint in ratio to the stroke width.
    Only works if `jointRounded` is `False`.

    - Type: `float`, optional
    - Default: `4`
    """

    billboard = traitlets.Bool(default_value=None, allow_none=True).tag(sync=True)
    """
    If `True`, extrude the path in screen space (width always faces the camera).
    If `False`, the width always faces up.

    - Type: `bool`, optional
    - Default: `False`
    """

    fade_trail = traitlets.Bool(default_value=None, allow_none=True).tag(sync=True)
    """Whether or not the path fades out.

    - Type: `bool`, optional
    - Default: `True`
    """

    trail_length = traitlets.Float(default_value=None, allow_none=True).tag(sync=True)
    """Trail length.

    - Type: `float`, optional
    - Default: `120`
    """

    _current_time = traitlets.Float(0).tag(sync=True)
    """The current time of the frame.

    - Type: `float`, optional
    - Default: set by the [`animate`][lonboard.experimental.TripsLayer.animate] method.

    !!! info
        This `_current_time` is not directly interpretable.

        Because of some technical details in deck.gl (the fact that deck.gl represents
        timestamps as `float32`), the `TripsLayer` automatically rescales the input
        timestamp data to a range representable by `float32`.
    """

    get_color = ColorAccessor(None, allow_none=True)
    """
    The color of each path in the format of `[r, g, b, [a]]`. Each channel is a number
    between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the color for all
          paths.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the color for the path at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_width = FloatAccessor(None, allow_none=True)
    """
    The width of each path, in units specified by `width_units` (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all paths.
        - If an array is provided, each value in the array will be used as the width for
          the path at the same row index.
    - Default: `1`.
    """

    get_timestamps = TimestampAccessor(None, allow_none=True)
    """
    The timestamp of each coordinate.

    - Type: [TimestampAccessor][lonboard.experimental.traits.TimestampAccessor]
    """

    def __init__(
        self,
        *,
        table: ArrowStreamExportable,
        get_timestamps: ArrowStreamExportable,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[TripsLayerKwargs],
    ) -> None:
        """Construct a TripsLayer from existing Arrow data.

        Args:
            table: An Arrow table from any Arrow-compatible library with a
                `geoarrow.linestring` geometry column.
            get_timestamps: An Arrow column or ChunkedArray with timestamps that
                correspond to the `LineString` geometries in the main table. This column
                must be a list-typed array containing a timestamp-typed child array.

        """
        super().__init__(
            table=table,
            _rows_per_chunk=_rows_per_chunk,
            get_timestamps=get_timestamps,  # type: ignore
            **kwargs,
        )

    @classmethod
    def from_geopandas(  # type: ignore
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        get_timestamps: ArrowStreamExportable,
        auto_downcast: bool = True,
        **kwargs: Unpack[TripsLayerKwargs],
    ) -> Self:
        return super().from_geopandas(
            gdf=gdf,
            auto_downcast=auto_downcast,
            get_timestamps=get_timestamps,  # type: ignore
            **kwargs,
        )

    @classmethod
    def from_duckdb(  # type: ignore
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        get_timestamps: ArrowStreamExportable,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[TripsLayerKwargs],
    ) -> Self:
        return super().from_duckdb(
            sql=sql,
            con=con,
            crs=crs,
            get_timestamps=get_timestamps,  # type: ignore
            **kwargs,
        )

    @classmethod
    def from_movingpandas(
        cls,
        traj_collection: TrajectoryCollection,
        **kwargs: Unpack[TripsLayerKwargs],
    ) -> Self:
        """Construct a TripsLayer from a MovingPandas
        [`TrajectoryCollection`][movingpandas.TrajectoryCollection].

        This is the simplest way to construct a `TripsLayer`. Under the hood, this
        constructor will convert the `TrajectoryCollection` to a GeoArrow table with a
        `LineString` geometry column for each row. It will also create a Timestamp Arrow
        column from the TrajectoryCollection's [`DatetimeIndex`][pandas.DatetimeIndex].

        Args:
            traj_collection: the trajectory collection

        Keyword Args:
            kwargs: keyword args to pass to the `TripsLayer` constructor.

        """
        from lonboard._geoarrow.movingpandas_interop import movingpandas_to_geoarrow

        (table, timestamp_col) = movingpandas_to_geoarrow(
            traj_collection=traj_collection,
        )
        return cls(table=table, get_timestamps=timestamp_col, **kwargs)

    def animate(
        self,
        *,
        step: timedelta,
        fps: float = 50,
        strftime_fmt: str | None = None,
    ) -> ipywidgets.widgets.widget_box.HBox:
        """Animate this layer with an
        [`ipywidgets.Play`][ipywidgets.widgets.widget_int.Play] controller.

        You can change how "fast" the animation is perceived by either increasing the
        amount of "data time" in each animation step, or by having more animation frames
        per second.

        As an example, passing `step=timedelta(seconds=60)` will set each time step of
        the animation to be 60 "data seconds". Setting `fps=50` (the default) causes
        there to be 50 animation frames per second.

        Note that for large data, it's possible there will be some rendering lag and
        data may not actually update at the desired frames per second.

        If you call `animate` multiple times, only the most recently produced `Play`
        widget will be active and linked to the map.

        Keyword Args:
            step: the length of time in the data to progress between each animation
                frame.
            fps: the number of animation frames per second. Defaults to `50`.
            strftime_fmt: the format string passed to
                [`datetime.strftime`][datetime.datetime.strftime]. Defaults to an
                inferred format string.

        Returns:
            an [`ipywidgets.HBox`][ipywidgets.widgets.widget_box.HBox] containing an
                [`ipywidgets.Play`][ipywidgets.widgets.widget_int.Play] controller to
                manage animation playback and an
                [`ipywidgets.Output`][ipywidgets.widgets.widget_output.Output] to
                display the current datetime of the map.

        """
        assert isinstance(step, timedelta), "expected step to be a timedelta."

        interval = 1000 / fps

        time_unit = self.get_timestamps.type.value_type.time_unit
        assert time_unit is not None

        # Convert the `step` into the units used by the timestamps on the layer.
        if time_unit == "s":
            resolved_step = step.total_seconds()
        elif time_unit == "ms":
            resolved_step = step.total_seconds() * 1000
        elif time_unit == "us":
            resolved_step = step.total_seconds() * 1000**2
        elif time_unit == "ns":
            resolved_step = step.total_seconds() * 1000**3
        else:
            assert False, f"Unexpected time unit {time_unit}"

        # Unlink any previous animation widget
        self.stop_animation()

        max_value = timestamp_max_physical_value(self.get_timestamps)
        play_widget = ipywidgets.Play(
            value=MIN_INTEGER_FLOAT32,
            min=MIN_INTEGER_FLOAT32,
            max=max_value,
            step=resolved_step,
            interval=interval,
            repeat=True,
        )

        timestamp_output = ipywidgets.Output()

        # Store a reference to the widget link
        self._animation_link = ipywidgets.jsdlink(
            (play_widget, "value"),
            (self, "_current_time"),
        )

        # Some callback prep done outside of the callback for perf
        tz_str: str | None = self.get_timestamps.type.value_type.tz

        # Custom datetime format without Z/local time because we append the tz string
        # below
        default_strftime = "%Y-%m-%d %H:%M:%S"
        if time_unit != "s":
            default_strftime += ".%f"

        def update_timestamp_output(change) -> None:
            current_datetime = self._current_time_to_datetime(change["new"])
            # Ignore timezone info because we also print tz str
            current_datetime.replace(tzinfo=None)

            if strftime_fmt is not None:
                s = current_datetime.strftime(strftime_fmt)
            else:
                s = current_datetime.strftime(default_strftime)

            if tz_str is not None:
                s += f" {tz_str}"

            timestamp_output.clear_output(wait=True)
            with timestamp_output:
                print(s)

        play_widget.observe(update_timestamp_output, names="value")

        return ipywidgets.HBox([play_widget, timestamp_output])

    @property
    def current_time(self) -> datetime:
        """Get the current time of the map as a `datetime` object.

        Returns:
            datetime object with current time.

        """
        return self._current_time_to_datetime(self._current_time)

    def _current_time_to_datetime(self, current_time: float) -> datetime:
        start_offset = timestamp_start_offset(self.get_timestamps)
        timestamp_int = int(current_time - start_offset)
        timestamp_scalar = Scalar(timestamp_int, type=DataType.int64()).cast(
            self.get_timestamps.type.value_type,
        )
        return timestamp_scalar.as_py()

    def stop_animation(self):
        """Stop any existing animation.

        This will
        [unlink](https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html#unlinking-widgets)
        the linking between the `Play` widget generated by `animate` and the layer.

        To reanimate the map, call [`animate`][lonboard.experimental.TripsLayer.animate]
        again.
        """
        if self._animation_link is not None:
            self._animation_link.unlink()
            self._animation_link = None

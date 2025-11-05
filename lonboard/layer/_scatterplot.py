from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._constants import EXTENSION_NAME
from lonboard.layer._base import BaseArrowLayer
from lonboard.traits import (
    ArrowTableTrait,
    ColorAccessor,
    FloatAccessor,
)

if TYPE_CHECKING:
    import sys

    import duckdb
    import geopandas as gpd
    import pyproj
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import ScatterplotLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class ScatterplotLayer(BaseArrowLayer):
    """The `ScatterplotLayer` renders circles at given coordinates.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, ScatterplotLayer

    # A GeoDataFrame with Point or MultiPoint geometries
    gdf = gpd.GeoDataFrame()
    layer = ScatterplotLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, ScatterplotLayer

    # Example: A FlatGeobuf file with Point or MultiPoint geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = ScatterplotLayer(
        table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[ScatterplotLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("scatterplot").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POINT, EXTENSION_NAME.MULTIPOINT},
    )
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    radius_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    radius_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    A global radius multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    radius_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum radius in pixels. This can be used to prevent the circle from getting
    too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    radius_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum radius in pixels. This can be used to prevent the circle from getting
    too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    A global line width multiplier for all points.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum line width in pixels. This can be used to prevent the stroke from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum line width in pixels. This can be used to prevent the stroke from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    stroked = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Draw the outline of points.

    - Type: `bool`, optional
    - Default: `False`
    """

    filled = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Draw the filled area of points.

    - Type: `bool`, optional
    - Default: `True`
    """

    billboard = t.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, rendered circles always face the camera. If `False` circles face up (i.e.
    are parallel with the ground plane).

    - Type: `bool`, optional
    - Default: `False`
    """

    antialiasing = t.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, circles are rendered with smoothed edges. If `False`, circles are
    rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping
    circles.

    - Type: `bool`, optional
    - Default: `True`
    """

    get_radius = FloatAccessor(None, allow_none=True)
    """
    The radius of each object, in units specified by `radius_units` (default
    `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the radius for all objects.
        - If an array is provided, each value in the array will be used as the radius
          for the object at the same row index.
    - Default: `1`.
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The filled color of each object in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the filled color for
          all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the filled color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The outline color of each object in the format of `[r, g, b, [a]]`. Each channel is
    a number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the outline color
          for all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each object, in units specified by `line_width_units`
    (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all objects.
        - If an array is provided, each value in the array will be used as the outline
          width for the object at the same row index.
    - Default: `1`.
    """

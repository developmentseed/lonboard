# ruff: noqa: D205

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

    from lonboard.types.layer import ColumnLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class ColumnLayer(BaseArrowLayer):
    """The ColumnLayer renders extruded cylinders (tessellated regular polygons) at given
    coordinates.
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[ColumnLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[ColumnLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[ColumnLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("column").tag(sync=True)

    table = ArrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point or MultiPoint column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.ScatterplotLayer.from_geopandas] instead.
    """

    disk_resolution = t.Int(None, allow_none=True).tag(sync=True)
    """
    The number of sides to render the disk as. The disk is a regular polygon that fits
    inside the given radius. A higher resolution will yield a smoother look close-up,
    but also need more resources to render.

    - Type: `int`, optional
    - Default: `20`
    """

    radius = t.Float(None, allow_none=True).tag(sync=True)
    """
    Disk size in units specified by `radius_units` (default meters).

    - Type: `float`, optional
    - Default: `1000`
    """

    angle = t.Float(None, allow_none=True).tag(sync=True)
    """
    Disk rotation, counter-clockwise in degrees.

    - Type: `float`, optional
    - Default: `0`
    """

    offset = t.Tuple(t.Float(), t.Float(), default_value=None, allow_none=True).tag(
        sync=True,
    )
    """
    Disk offset from the position, relative to the radius. By default, the disk is
    centered at each position.

    - Type: `tuple[float, float]`, optional
    - Default: `(0, 0)`
    """

    coverage = t.Float(None, allow_none=True).tag(sync=True)
    """
    Radius multiplier, between 0 - 1. The radius of the disk is calculated by
    `coverage * radius`

    - Type: `float`, optional
    - Default: `1`
    """

    elevation_scale = t.Float(None, allow_none=True).tag(sync=True)
    """
    Column elevation multiplier. The elevation of column is calculated by
    `elevation_scale * get_elevation(d)`. `elevation_scale` is a handy property
    to scale all column elevations without updating the data.

    - Type: `float`, optional
    - Default: `1`
    """

    filled = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to draw a filled column (solid fill).

    - Type: `bool`, optional
    - Default: `True`
    """

    stroked = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to draw an outline around the disks. Only applies if `extruded=False`.

    - Type: `bool`, optional
    - Default: `False`
    """

    extruded = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to extrude the columns. If set to `false`, all columns will be rendered as
    flat polygons.

    - Type: `bool`, optional
    - Default: `True`
    """

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the column. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex around the disk. Only applies if `extruded=True`.

    - Type: `bool`, optional
    - Default: `False`
    """

    flat_shading = t.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, the vertical surfaces of the columns use [flat
    shading](https://en.wikipedia.org/wiki/Shading#Flat_vs._smooth_shading). If `false`,
    use smooth shading. Only effective if `extruded` is `True`.

    - Type: `bool`, optional
    - Default: `False`
    """

    radius_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
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
    The line width multiplier that multiplied to all outlines if the `stroked` attribute
    is `True`.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum outline width in pixels. This can be used to prevent the line from
    getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum outline width in pixels. This can be used to prevent the line from
    getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
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
        - If a single `list` or `tuple` is provided, it is used as the outline color for
          all objects.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the object at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_elevation = FloatAccessor(None, allow_none=True)
    """
    The elevation of each cell in meters.

    Only applies if `extruded=True`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all polygons.
        - If an array is provided, each value in the array will be used as the width for
          the polygon at the same row index.
    - Default: `1000`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each column, in units specified by `line_width_units`
    (default `'meters'`). Only applies if `extruded: false` and `stroked: true`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all columns.
        - If an array is provided, each value in the array will be used as the outline
          width for the column at the same row index.
    - Default: `1`.
    """

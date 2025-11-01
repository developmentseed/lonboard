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

    from lonboard.types.layer import PolygonLayerKwargs, SolidPolygonLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class PolygonLayer(BaseArrowLayer):
    """The `PolygonLayer` renders filled, stroked and/or extruded polygons.

    !!! note

        This layer is essentially a combination of a [`PathLayer`][lonboard.PathLayer]
        and a [`SolidPolygonLayer`][lonboard.SolidPolygonLayer]. This has some overhead
        beyond a `SolidPolygonLayer`, so if you're looking for the maximum performance
        with large data, you may want to use a `SolidPolygonLayer` directly.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PolygonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = PolygonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 100, 100, 150],
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, PolygonLayer

    # Example: A FlatGeobuf file with Polygon or MultiPolygon geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = PolygonLayer(
        table,
        get_fill_color=[255, 0, 0],
        get_line_color=[0, 100, 100, 150],
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[PolygonLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PolygonLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[PolygonLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("polygon").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON},
    )
    """A GeoArrow table with a Polygon or MultiPolygon column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PolygonLayer.from_geopandas] instead.
    """

    stroked = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw an outline around the polygon (solid fill).

    Note that both the outer polygon as well the outlines of any holes will be drawn.

    - Type: `bool`, optional
    - Default: `True`
    """

    filled = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to draw a filled polygon (solid fill).

    Note that only the area between the outer polygon and any holes will be filled.

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to extrude the polygons.

    Based on the elevations provided by the `getElevation` accessor.

    If set to `false`, all polygons will be flat, this generates less geometry and is
    faster than simply returning 0 from getElevation.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the polygon. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex on the polygon.

    - Type: `bool`, optional
    - Default: `False`

    **Remarks:**

    - These lines are rendered with `GL.LINE` and will thus always be 1 pixel wide.
    - Wireframe and solid extrusions are exclusive, you'll need to create two layers
      with the same data if you want a combined rendering effect.
    """

    elevation_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """Elevation multiplier.

    The final elevation is calculated by `elevationScale * getElevation(d)`.
    `elevationScale` is a handy property to scale all elevation without updating the
    data.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the outline width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    line_width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The outline width multiplier that multiplied to all outlines of `Polygon` and
    `MultiPolygon` features if the `stroked` attribute is true.

    - Type: `float`, optional
    - Default: `1`
    """

    line_width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum outline width in pixels. This can be used to prevent the outline from
    getting too small when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    line_width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum outline width in pixels. This can be used to prevent the outline from
    getting too big when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    line_joint_rounded = t.Bool(None, allow_none=True).tag(sync=True)
    """Type of joint. If `true`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    line_miter_limit = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """The maximum extent of a joint in ratio to the stroke width.

    Only works if `line_joint_rounded` is false.

    - Type: `float`, optional
    - Default: `4`
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The fill color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the fill color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the fill color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The outline color of each polygon in the format of `[r, g, b, [a]]`. Each channel is
    a number between 0-255 and `a` is 255 if not supplied.

    Only applies if `stroked=True`.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the outline color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the outline color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_width = FloatAccessor(None, allow_none=True)
    """
    The width of the outline of each polygon, in units specified by `line_width_units`
    (default `'meters'`).

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the outline width for all polygons.
        - If an array is provided, each value in the array will be used as the outline
          width for the polygon at the same row index.
    - Default: `1`.
    """

    get_elevation = FloatAccessor(None, allow_none=True)
    """
    The elevation to extrude each polygon with, in meters.

    Only applies if `extruded=True`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all polygons.
        - If an array is provided, each value in the array will be used as the width for
          the polygon at the same row index.
    - Default: `1000`.
    """


class SolidPolygonLayer(BaseArrowLayer):
    """The `SolidPolygonLayer` renders filled and/or extruded polygons.

    !!! note

        This layer is similar to the [`PolygonLayer`][lonboard.PolygonLayer] but will
        not render an outline around polygons. In most cases, you'll want to use the
        `PolygonLayer` directly, but for very large datasets not drawing the outline can
        significantly improve performance, in which case you may want to use this layer.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, SolidPolygonLayer

    # A GeoDataFrame with Polygon or MultiPolygon geometries
    gdf = gpd.GeoDataFrame()
    layer = SolidPolygonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, SolidPolygonLayer

    # Example: A FlatGeobuf file with Polygon or MultiPolygon geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = SolidPolygonLayer(
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
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[SolidPolygonLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("solid-polygon").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POLYGON, EXTENSION_NAME.MULTIPOLYGON},
    )
    """A GeoArrow table with a Polygon or MultiPolygon column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.SolidPolygonLayer.from_geopandas] instead.
    """

    filled = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to fill the polygons (based on the color provided by the
    `get_fill_color` accessor).

    - Type: `bool`, optional
    - Default: `True`
    """

    extruded = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to extrude the polygons (based on the elevations provided by the
    `get_elevation` accessor'). If set to `False`, all polygons will be flat, this
    generates less geometry and is faster than simply returning `0` from
    `get_elevation`.

    - Type: `bool`, optional
    - Default: `False`
    """

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Whether to generate a line wireframe of the polygon. The outline will have
    "horizontal" lines closing the top and bottom polygons and a vertical line
    (a "strut") for each vertex on the polygon.

    - Type: `bool`, optional
    - Default: `False`

    **Remarks:**

    - These lines are rendered with `GL.LINE` and will thus always be 1 pixel wide.
    - Wireframe and solid extrusions are exclusive, you'll need to create two layers
      with the same data if you want a combined rendering effect.
    """

    elevation_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    Elevation multiplier. The final elevation is calculated by `elevation_scale *
    get_elevation(d)`. `elevation_scale` is a handy property to scale all elevation
    without updating the data.

    - Type: `float`, optional
    - Default: `1`
    """

    get_elevation = FloatAccessor(None, allow_none=True)
    """
    The elevation to extrude each polygon with, in meters.

    Only applies if `extruded=True`.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the width for all polygons.
        - If an array is provided, each value in the array will be used as the width for
          the polygon at the same row index.
    - Default: `1000`.
    """

    get_fill_color = ColorAccessor(None, allow_none=True)
    """
    The fill color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the fill color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the fill color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

    get_line_color = ColorAccessor(None, allow_none=True)
    """
    The line color of each polygon in the format of `[r, g, b, [a]]`. Each channel is a
    number between 0-255 and `a` is 255 if not supplied.

    Only applies if `extruded=True`.

    - Type: [ColorAccessor][lonboard.traits.ColorAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the line color for
          all polygons.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the line color for the polygon at the same row index.
    - Default: `[0, 0, 0, 255]`.
    """

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

    from lonboard.types.layer import PathLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class PathLayer(BaseArrowLayer):
    """The `PathLayer` renders lists of coordinate points as extruded polylines with
    mitering.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PathLayer

    # A GeoDataFrame with LineString or MultiLineString geometries
    gdf = gpd.GeoDataFrame()
    layer = PathLayer.from_geopandas(
        gdf,
        get_color=[255, 0, 0],
        width_min_pixels=2,
    )
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, PathLayer

    # Example: A FlatGeobuf file with LineString or MultiLineString geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = PathLayer(
        table,
        get_color=[255, 0, 0],
        width_min_pixels=2,
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[PathLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PathLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[PathLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("path").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={
            EXTENSION_NAME.LINESTRING,
            EXTENSION_NAME.MULTILINESTRING,
        },
    )
    """A GeoArrow table with a LineString or MultiLineString column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PathLayer.from_geopandas] instead.
    """

    width_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'meters'`
    """

    width_scale = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The path width multiplier that multiplied to all paths.

    - Type: `float`, optional
    - Default: `1`
    """

    width_min_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The minimum path width in pixels. This prop can be used to prevent the path from
    getting too thin when zoomed out.

    - Type: `float`, optional
    - Default: `0`
    """

    width_max_pixels = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    The maximum path width in pixels. This prop can be used to prevent the path from
    getting too thick when zoomed in.

    - Type: `float`, optional
    - Default: `None`
    """

    joint_rounded = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Type of joint. If `True`, draw round joints. Otherwise draw miter joints.

    - Type: `bool`, optional
    - Default: `False`
    """

    cap_rounded = t.Bool(None, allow_none=True).tag(sync=True)
    """
    Type of caps. If `True`, draw round caps. Otherwise draw square caps.

    - Type: `bool`, optional
    - Default: `False`
    """

    miter_limit = t.Int(None, allow_none=True).tag(sync=True)
    """
    The maximum extent of a joint in ratio to the stroke width.
    Only works if `jointRounded` is `False`.

    - Type: `float`, optional
    - Default: `4`
    """

    billboard = t.Bool(None, allow_none=True).tag(sync=True)
    """
    If `True`, extrude the path in screen space (width always faces the camera).
    If `False`, the width always faces up.

    - Type: `bool`, optional
    - Default: `False`
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

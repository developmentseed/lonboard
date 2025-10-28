from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t

from lonboard._constants import EXTENSION_NAME
from lonboard.layer._base import BaseArrowLayer
from lonboard.traits import (
    ArrowTableTrait,
    ColorAccessor,
    NormalAccessor,
)

if TYPE_CHECKING:
    import sys

    import duckdb
    import geopandas as gpd
    import pyproj
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import PointCloudLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class PointCloudLayer(BaseArrowLayer):
    """The `PointCloudLayer` renders a point cloud with 3D positions, normals and colors.

    The `PointCloudLayer` can be more efficient at rendering large quantities of points
    than the [`ScatterplotLayer`][lonboard.ScatterplotLayer], but has fewer rendering
    options. In particular, you can have only one point size across all points in your
    data.

    **Example:**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, PointCloudLayer

    # A GeoDataFrame with Point geometries
    gdf = gpd.GeoDataFrame()
    layer = PointCloudLayer.from_geopandas(
        gdf,
        get_color=[255, 0, 0],
        point_size=2,
    )
    m = Map(layer)
    ```
    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        *,
        _rows_per_chunk: int | None = None,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ) -> None:
        super().__init__(table=table, _rows_per_chunk=_rows_per_chunk, **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[PointCloudLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("point-cloud").tag(sync=True)

    table = ArrowTableTrait(
        allowed_geometry_types={EXTENSION_NAME.POINT},
        allowed_dimensions={3},
    )
    """A GeoArrow table with a Point column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.PointCloudLayer.from_geopandas] instead.
    """

    size_units = t.Unicode(None, allow_none=True).tag(sync=True)
    """
    The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See
    [unit
    system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

    - Type: `str`, optional
    - Default: `'pixels'`
    """

    point_size = t.Float(None, allow_none=True, min=0).tag(sync=True)
    """
    Global radius of all points, in units specified by `size_units`.

    - Type: `float`, optional
    - Default: `10`
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

    get_normal = NormalAccessor(None, allow_none=True)
    """
    The normal of each object, in `[nx, ny, nz]`.

    - Type: [NormalAccessor][lonboard.traits.NormalAccessor], optional
        - If a single `list` or `tuple` is provided, it is used as the normal for all
          points.
        - If a numpy or pyarrow array is provided, each value in the array will be used
          as the normal for the point at the same row index.
    - Default: `1`.
    """

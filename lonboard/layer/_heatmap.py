from __future__ import annotations

from typing import TYPE_CHECKING

import traitlets as t
from arro3.core import Table

from lonboard._constants import EXTENSION_NAME
from lonboard.layer._base import BaseArrowLayer
from lonboard.traits import (
    ArrowTableTrait,
    FloatAccessor,
    VariableLengthTuple,
)

if TYPE_CHECKING:
    import sys

    import duckdb
    import geopandas as gpd
    import pyproj
    from arro3.core.types import ArrowStreamExportable

    from lonboard.types.layer import HeatmapLayerKwargs

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


class HeatmapLayer(BaseArrowLayer):
    """The `HeatmapLayer` visualizes the spatial distribution of data.

    **Example**

    From GeoPandas:

    ```py
    import geopandas as gpd
    from lonboard import Map, HeatmapLayer

    # A GeoDataFrame with Point geometries
    gdf = gpd.GeoDataFrame()
    layer = HeatmapLayer.from_geopandas(gdf)
    m = Map(layer)
    ```

    From an Arrow-compatible source like [pyogrio][pyogrio] or [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest):

    ```py
    from geoarrow.rust.io import read_flatgeobuf
    from lonboard import Map, HeatmapLayer

    # Example: A FlatGeobuf file with Point geometries
    table = read_flatgeobuf("path/to/file.fgb")
    layer = HeatmapLayer(
        table,
        get_fill_color=[255, 0, 0],
    )
    m = Map(layer)
    ```

    """

    def __init__(
        self,
        table: ArrowStreamExportable,
        **kwargs: Unpack[HeatmapLayerKwargs],
    ) -> None:
        # NOTE: we override the default for _rows_per_chunk because otherwise we render
        # one heatmap per _chunk_ not for the entire dataset (we don't have a way to
        # concat batches in the frontend)
        table_o3 = Table.from_arrow(table)
        super().__init__(table=table, _rows_per_chunk=len(table_o3), **kwargs)

    @classmethod
    def from_geopandas(
        cls,
        gdf: gpd.GeoDataFrame,
        *,
        auto_downcast: bool = True,
        **kwargs: Unpack[HeatmapLayerKwargs],
    ) -> Self:
        return super().from_geopandas(gdf=gdf, auto_downcast=auto_downcast, **kwargs)

    @classmethod
    def from_duckdb(
        cls,
        sql: str | duckdb.DuckDBPyRelation,
        con: duckdb.DuckDBPyConnection | None = None,
        *,
        crs: str | pyproj.CRS | None = None,
        **kwargs: Unpack[HeatmapLayerKwargs],
    ) -> Self:
        return super().from_duckdb(sql=sql, con=con, crs=crs, **kwargs)

    _layer_type = t.Unicode("heatmap").tag(sync=True)

    table = ArrowTableTrait(allowed_geometry_types={EXTENSION_NAME.POINT})
    """A GeoArrow table with a Point column.

    This is the fastest way to plot data from an existing GeoArrow source, such as
    [geoarrow-rust](https://geoarrow.github.io/geoarrow-rs/python/latest) or
    [geoarrow-pyarrow](https://geoarrow.github.io/geoarrow-python/main/index.html).

    If you have a GeoPandas `GeoDataFrame`, use
    [`from_geopandas`][lonboard.HeatmapLayer.from_geopandas] instead.
    """

    radius_pixels = t.Float(None, allow_none=True).tag(sync=True)
    """Radius of the circle in pixels, to which the weight of an object is distributed.

    - Type: `float`, optional
    - Default: `30`
    """

    # TODO: stabilize ColormapTrait
    # color_range?: Color[];
    # """Specified as an array of colors [color1, color2, ...].

    # - Default: `6-class YlOrRd` - [colorbrewer](http://colorbrewer2.org/#type=sequential&scheme=YlOrRd&n=6)
    # """

    intensity = t.Float(None, allow_none=True).tag(sync=True)
    """
    Value that is multiplied with the total weight at a pixel to obtain the final
    weight.

    - Type: `float`, optional
    - Default: `1`
    """

    threshold = t.Float(None, allow_none=True, min=0, max=1).tag(sync=True)
    """Ratio of the fading weight to the max weight, between `0` and `1`.

    For example, `0.1` affects all pixels with weight under 10% of the max.

    Ignored when `color_domain` is specified.

    - Type: `float`, optional
    - Default: `0.05`
    """

    color_domain = VariableLengthTuple(
        t.Float(),
        default_value=None,
        allow_none=True,
        minlen=2,
        maxlen=2,
    ).tag(sync=True)
    # """
    # Controls how weight values are mapped to the `color_range`, as an array of two
    # numbers [`min_value`, `max_value`].

    # - Type: `(float, float)`, optional
    # - Default: `None`
    # """

    aggregation = t.Unicode(None, allow_none=True).tag(sync=True)
    """Defines the type of aggregation operation

    Valid values are 'SUM', 'MEAN'.

    - Type: `str`, optional
    - Default: `"SUM"`
    """

    weights_texture_size = t.Int(None, allow_none=True).tag(sync=True)
    """Specifies the size of weight texture.

    - Type: `int`, optional
    - Default: `2048`
    """

    debounce_timeout = t.Int(None, allow_none=True).tag(sync=True)
    """
    Interval in milliseconds during which changes to the viewport don't trigger
    aggregation.

    - Type: `int`, optional
    - Default: `500`
    """

    get_weight = FloatAccessor(None, allow_none=True)
    """The weight of each object.

    - Type: [FloatAccessor][lonboard.traits.FloatAccessor], optional
        - If a number is provided, it is used as the weight for all objects.
        - If an array is provided, each value in the array will be used as the weight
          for the object at the same row index.
    - Default: `1`.
    """

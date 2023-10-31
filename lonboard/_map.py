from __future__ import annotations

from pathlib import Path

import anywidget
import ipywidgets
import traitlets

from lonboard._layer import BaseLayer
from lonboard._viewport import compute_view

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"


class Map(anywidget.AnyWidget):
    """
    The top-level class used to display a map in a Jupyter Widget.

    **Example:**

    ```py
    import geopandas as gpd
    from lonboard import Map, ScatterplotLayer, SolidPolygonLayer

    # A GeoDataFrame with Point geometries
    point_gdf = gpd.GeoDataFrame()
    point_layer = ScatterplotLayer.from_geopandas(
        point_gdf,
        get_fill_color=[255, 0, 0],
    )

    # A GeoDataFrame with Polygon geometries
    polygon_gdf = gpd.GeoDataFrame()
    polygon_layer = SolidPolygonLayer.from_geopandas(
        gdf,
        get_fill_color=[255, 0, 0],
    )

    map_ = Map(layers=[point_layer, polygon_layer])
    ```
    """

    _esm = bundler_output_dir / "index.js"
    _css = bundler_output_dir / "index.css"

    _initial_view_state = traitlets.Dict().tag(sync=True)
    """
    The initial view state of the map.

    - Type: `dict`, optional
    - Default: Automatically inferred from the data passed to the map.

    The keys _must_ include:

    - `longitude`: longitude at the map center.
    - `latitude`: latitude at the map center.
    - `zoom`: zoom level.

    Keys may additionally include:

    - `pitch` (float, optional) - pitch angle in degrees. Default `0` (top-down).
    - `bearing` (float, optional) - bearing angle in degrees. Default `0` (north).
    - `maxZoom` (float, optional) - max zoom level. Default `20`.
    - `minZoom` (float, optional) - min zoom level. Default `0`.
    - `maxPitch` (float, optional) - max pitch angle. Default `60`.
    - `minPitch` (float, optional) - min pitch angle. Default `0`.

    Note that currently no camel-case/snake-case translation occurs for this method, and
    so keys must be in camel case.

    This API is not yet stabilized and may change in the future.
    """

    _height = traitlets.Int(500).tag(sync=True)
    """Height of the map in pixels.

    This API is not yet stabilized and may change in the future.
    """

    layers = traitlets.List(trait=traitlets.Instance(BaseLayer)).tag(
        sync=True, **ipywidgets.widget_serialization
    )
    """One or more `Layer` objects to display on this map.
    """

    show_tooltip = traitlets.Bool(True).tag(sync=True)
    """
    Whether to render a tooltip on hover on the map.

    - Type: `bool`
    - Default: `True`
    """

    @traitlets.default("_initial_view_state")
    def _default_initial_view_state(self):
        tables = [layer.table for layer in self.layers]
        return compute_view(tables)

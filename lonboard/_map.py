from __future__ import annotations

from pathlib import Path
from typing import Union

import ipywidgets
import traitlets
from ipywidgets.embed import embed_minimal_html

from lonboard._base import BaseAnyWidget
from lonboard._layer import BaseLayer
from lonboard._serialization import VIEW_STATE_SERIALIZATION
from lonboard._viewport import ViewState, compute_view
from lonboard.traits import _ObservableInstance

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"


class Map(BaseAnyWidget):
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

    _view_state = _ObservableInstance(ViewState).tag(
        sync=True,
        **VIEW_STATE_SERIALIZATION,
    )
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

    def to_html(self, filename: Union[str, Path]) -> None:
        """Save the current map as a standalone HTML file.

        Args:
            filename: where to save the generated HTML file.
        """
        embed_minimal_html(filename, views=[self], drop_defaults=False)

    @traitlets.default("_view_state")
    def _default_initial_view_state(self):
        tables = [layer.table for layer in self.layers]
        return compute_view(tables)

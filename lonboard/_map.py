from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

import ipywidgets
import traitlets
from ipywidgets.embed import embed_minimal_html

from lonboard._base import BaseAnyWidget
from lonboard._environment import DEFAULT_HEIGHT
from lonboard._layer import BaseLayer
from lonboard._viewport import compute_view
from lonboard.basemap import CartoBasemap

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

    m = Map([point_layer, polygon_layer])
    ```
    """

    def __init__(self, layers: Union[BaseLayer, Sequence[BaseLayer]], **kwargs) -> None:
        """Create a new Map.

        Aside from the `layers` argument, pass keyword arguments for any other attribute
        defined in this class.

        Args:
            layers: One or more layers to render on this map.

        Returns:
            A Map object.
        """
        if isinstance(layers, BaseLayer):
            layers = [layers]

        super().__init__(layers=layers, **kwargs)

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

    _height = traitlets.Int(default_value=DEFAULT_HEIGHT, allow_none=True).tag(
        sync=True
    )
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

    picking_radius = traitlets.Int(5).tag(sync=True)
    """
    Extra pixels around the pointer to include while picking (such as for a tooltip).

    This is helpful when rendered objects are difficult to target, for example
    irregularly shaped icons, small moving circles or interaction by touch.

    - Type: `int`
    - Default: `5`
    """

    basemap_style = traitlets.Unicode(CartoBasemap.PositronNoLabels).tag(sync=True)
    """
    A MapLibre-compatible basemap style.

    Various styles are provided in [`lonboard.basemap`](https://developmentseed.org/lonboard/latest/api/basemap/).

    - Type: `str`
    - Default
      [`lonboard.basemap.CartoBasemap.PositronNoLabels`][lonboard.basemap.CartoBasemap.PositronNoLabels]
    """

    def to_html(self, filename: Union[str, Path]) -> None:
        """Save the current map as a standalone HTML file.

        Args:
            filename: where to save the generated HTML file.
        """
        embed_minimal_html(filename, views=[self], drop_defaults=False)

    @traitlets.default("_initial_view_state")
    def _default_initial_view_state(self):
        return compute_view(self.layers)

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Optional, Sequence, TextIO, Union, overload

import ipywidgets
import traitlets
from ipywidgets.embed import embed_minimal_html

from lonboard._base import BaseAnyWidget
from lonboard._environment import DEFAULT_HEIGHT
from lonboard._layer import BaseLayer
from lonboard._viewport import compute_view
from lonboard.basemap import CartoBasemap
from lonboard.traits import (
    DEFAULT_INITIAL_VIEW_STATE,
    BasemapUrl,
    VariableLengthTuple,
    ViewStateTrait,
)
from lonboard.types.map import MapKwargs

if TYPE_CHECKING:
    from IPython.display import HTML  # type: ignore

    if sys.version_info >= (3, 12):
        from typing import Unpack
    else:
        from typing_extensions import Unpack


# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"

# HTML template to override exported map as 100% height
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<style>
    html {{ height: 100%; }}
    body {{ height: 100%; }}
    .widget-subarea {{ height: 100%; }}
    .jupyter-widgets-disconnected {{ height: 100%; }}
</style>
<body>
{snippet}
</body>
</html>
"""


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

    def __init__(
        self, layers: Union[BaseLayer, Sequence[BaseLayer]], **kwargs: Unpack[MapKwargs]
    ) -> None:
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

    view_state = ViewStateTrait()
    """
    The view state of the map.

    - Type: [`ViewState`][lonboard.models.ViewState]
    - Default: Automatically inferred from the data passed to the map.

    You can initialize the map to a specific view state using this property:

    ```py
    Map(
        layers,
        view_state={"longitude": -74.0060, "latitude": 40.7128, "zoom": 7}
    )
    ```

    !!! note

        The properties of the view state are immutable. Use
        [`set_view_state`][lonboard.Map.set_view_state] to modify a map's view state
        once it's been initially rendered.

    """

    _height = traitlets.Int(default_value=DEFAULT_HEIGHT, allow_none=True).tag(
        sync=True
    )
    """Height of the map in pixels.

    This API is not yet stabilized and may change in the future.
    """

    layers = VariableLengthTuple(traitlets.Instance(BaseLayer)).tag(
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

    basemap_style = BasemapUrl(CartoBasemap.PositronNoLabels)
    """
    A URL to a MapLibre-compatible basemap style.

    Various styles are provided in [`lonboard.basemap`](https://developmentseed.org/lonboard/latest/api/basemap/).

    - Type: `str`, holding a URL hosting a basemap style.
    - Default
      [`lonboard.basemap.CartoBasemap.PositronNoLabels`][lonboard.basemap.CartoBasemap.PositronNoLabels]
    """

    custom_attribution = traitlets.Union(
        [
            traitlets.Unicode(allow_none=True),
            VariableLengthTuple(traitlets.Unicode(allow_none=False)),
        ]
    ).tag(sync=True)
    """
    Custom attribution to display on the map.

    This attribute supports the same format as the `attribution` property in the
    Maplibre API.

    - Type: `str` or `List[str]`
    - Default: `None`

    You can provide either a single string or a list of strings for custom attributions.
    If an attribution value is set in the map style, it will be displayed in addition to
    this custom attribution.

    **Example:**

        ```py
        m = Map(
            layers,
            custom_attribution="Development Seed"
        )
        ```

    **Example:**

        ```py
        m = Map(
            layers,
            custom_attribution=["Development Seed", "OpenStreetMap"]
        )
        ```
    """

    # TODO: We'd prefer a "Strict union of bool and float" but that doesn't
    # work here because `Union[bool, float]` would coerce `1` to `True`, which we don't
    # want, and `Union[float, bool]` would coerce `True` to `1`, which we also don't
    # want.
    # In the future we could create a custom trait for this if asked for.
    use_device_pixels = traitlets.Any(allow_none=True, default_value=None).tag(
        sync=True
    )
    """Controls the resolution of the drawing buffer used for rendering.

    Setting this to `false` or a number <= 1 will improve performance on high resolution
    displays.

    **Note**: This parameter must be passed to the `Map()` constructor. It cannot be
    changed once the map has been created.

    The available options are:

    - `true`: Device (physical) pixels resolution is used for rendering, this resolution
      is defined by `window.devicePixelRatio`. On Retina/HD systems this resolution is
      usually twice as big as CSS pixels resolution.
    - `false`: CSS pixels resolution (equal to the canvas size) is used for rendering.
    - `Number` (Experimental): Specified Number is used as a custom ratio (drawing
      buffer resolution to CSS pixel resolution) to determine drawing buffer size, a
      value less than one uses resolution smaller than CSS pixels, gives better
      performance but produces blurry images, a value greater than one uses resolution
      bigger than CSS pixels resolution (canvas size), produces sharp images but at a
      lower performance.

    - Type: `float`, `int` or `bool`
    - Default: `true`
    """

    parameters = traitlets.Any(allow_none=True, default_value=None).tag(sync=True)
    """GPU parameters to pass to deck.gl.

    **This is an advanced API. The vast majority of users should not need to touch this
    setting.**

    !!! Note

        The docstring below is copied from upstream deck.gl documentation. Any usage of
        `GL` refers to the constants defined in [`@luma.gl/constants`
        here](https://github.com/visgl/luma.gl/blob/master/modules/constants/src/webgl-constants.ts),
        which comes from the [MDN docs
        here](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Constants).

        In place of any `GL` constant, you can use the underlying integer it represents.
        For example, instead of the JS

        ```
        depthFunc: GL.LEQUAL
        ```

        referring to the [MDN
        docs](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Constants#depth_or_stencil_tests),
        you should use

        ```
        depthFunc: 0x0203
        ```

        Note that these parameters do not yet work with integer keys. If you would like
        to use integer keys, open an issue.

    Expects an object with GPU parameters. Before each frame is rendered, this object
    will be passed to luma.gl's `setParameters` function to reset the GPU context
    parameters, e.g. to disable depth testing, change blending modes etc. The default
    parameters set by `Deck` on initialization are the following:

    ```js
    {
      blend: true,
      blendFunc: [GL.SRC_ALPHA, GL.ONE_MINUS_SRC_ALPHA, GL.ONE, GL.ONE_MINUS_SRC_ALPHA],
      polygonOffsetFill: true,
      depthTest: true,
      depthFunc: GL.LEQUAL
    }
    ```

    Refer to the luma.gl
    [setParameters](https://github.com/visgl/luma.gl/blob/8.5-release/modules/gltools/docs/api-reference/parameter-setting.md)
    API for documentation on supported parameters and values.

    ```js
    import GL from '@luma.gl/constants';
    new Deck({
      // ...
      parameters: {
        blendFunc: [GL.ONE, GL.ONE, GL.ONE, GL.ONE],
        depthTest: false
      }
    });
    ```

    Notes:

    - Any GPU `parameters` prop supplied to individual layers will still override the
      global `parameters` when that layer is rendered.
    """

    def add_layer(
        self,
        layers: BaseLayer | Sequence[BaseLayer] | Map,
        *,
        focus: bool = False,
        reset_zoom: bool = False,
    ):
        """Add one or more new layers to the map.

        Examples:

        ```py
        from lonboard import viz

        m = viz(some_data)
        m.add_layer(viz(more_data), focus=True)
        ```

        Args:
            layers: New layers to add to the map. This can be:
                - a layer instance
                - a list or tuple of layer instances
                - another `Map` instance, in which case its layers will be added to this
                  map. This lets you pass the result of `viz` into this method.

            focus: If True, set the view state of the map based on the _newly-added_
                layers. Defaults to False.
            reset_zoom: If True, set the view state of the map based on _all_ layers.
                Defaults to False.

        Raises:
            ValueError: _description_
        """

        if focus and reset_zoom:
            raise ValueError("focus and reset_zoom may not both be set.")

        if isinstance(layers, Map):
            new_layers = layers.layers
            self.layers += layers.layers
            # self.layers =x
            # layers = layers.layers
        elif isinstance(layers, BaseLayer):
            new_layers = (layers,)
            layers = [layers]
            self.layers += (layers,)
        else:
            new_layers = tuple(layers)
            self.layers += tuple(layers)

        self.layers += new_layers

        # self.layers += tuple(layers)

        if focus:
            self.view_state = compute_view(new_layers)  # type: ignore

        elif reset_zoom:
            self.view_state = compute_view(self.layers)  # type: ignore

    def set_view_state(
        self,
        *,
        longitude: Optional[float] = None,
        latitude: Optional[float] = None,
        zoom: Optional[float] = None,
        pitch: Optional[float] = None,
        bearing: Optional[float] = None,
    ) -> None:
        """Set the view state of the map.

        Any parameters that are unset will not be changed.

        Keyword Args:
            longitude: the new longitude to set on the map. Defaults to None.
            latitude: the new latitude to set on the map. Defaults to None.
            zoom: the new zoom to set on the map. Defaults to None.
            pitch: the new pitch to set on the map. Defaults to None.
            bearing: the new bearing to set on the map. Defaults to None.
        """
        view_state = (
            self.view_state._asdict()  # type: ignore
            if self.view_state is not None
            else DEFAULT_INITIAL_VIEW_STATE
        )

        if longitude is not None:
            view_state["longitude"] = longitude
        if latitude is not None:
            view_state["latitude"] = latitude
        if zoom is not None:
            view_state["zoom"] = zoom
        if pitch is not None:
            view_state["pitch"] = pitch
        if bearing is not None:
            view_state["bearing"] = bearing

        self.view_state = view_state

    def fly_to(
        self,
        *,
        longitude: Union[int, float],
        latitude: Union[int, float],
        zoom: Union[int, float],
        duration: int = 4000,
        pitch: Union[int, float] = 0,
        bearing: Union[int, float] = 0,
        curve: Optional[Union[int, float]] = None,
        speed: Optional[Union[int, float]] = None,
        screen_speed: Optional[Union[int, float]] = None,
    ):
        """ "Fly" the map to a new location.

        Args:
            longitude: The longitude of the new viewport.
            latitude: The latitude of the new viewport.
            zoom: The zoom of the new viewport.
            pitch: The pitch of the new viewport. Defaults to 0.
            bearing: The bearing of the new viewport. Defaults to 0.
            duration: The number of milliseconds for the viewport transition to take.
                Defaults to 4000.
            curve: The zooming "curve" that will occur along the flight path. Default
                `1.414`.
            speed: The average speed of the animation defined in relation to
                `curve`, it linearly affects the duration, higher speed returns smaller
                durations and vice versa. Default `1.2`.
            screen_speed: The average speed of the animation measured in screenfuls per
                second. Similar to speed it linearly affects the duration, when
                specified speed is ignored.
        """
        if not isinstance(longitude, (int, float)):
            raise TypeError(
                f"Expected longitude to be an int or float, got {type(longitude)}"
            )

        if not isinstance(latitude, (int, float)):
            raise TypeError(
                f"Expected latitude to be an int or float, got {type(latitude)}"
            )

        if not isinstance(zoom, (int, float)):
            raise TypeError(f"Expected zoom to be an int or float, got {type(zoom)}")

        data = {
            "type": "fly-to",
            "longitude": longitude,
            "latitude": latitude,
            "zoom": zoom,
            "pitch": pitch,
            "bearing": bearing,
            "transitionDuration": duration,
            "curve": curve,
            "speed": speed,
            "screenSpeed": screen_speed,
        }
        self.send(data)

    @overload
    def to_html(
        self,
        filename: None = None,
        title: Optional[str] = None,
    ) -> str: ...

    @overload
    def to_html(
        self,
        filename: Union[str, Path, TextIO, IO[str]],
        title: Optional[str] = None,
    ) -> None: ...

    def to_html(
        self,
        filename: Union[str, Path, TextIO, IO[str], None] = None,
        title: Optional[str] = None,
    ) -> Union[None, str]:
        """Save the current map as a standalone HTML file.

        Args:
            filename: where to save the generated HTML file.

        Keyword Args:
            title: A title for the exported map. This will show as the browser tab name.

        Returns:
            If `filename` is not passed, returns the HTML content as a `str`.
        """

        def inner(fp):
            embed_minimal_html(
                fp,
                views=[self],
                title=title or "Lonboard export",
                template=_HTML_TEMPLATE,
                drop_defaults=False,
            )

        if filename is None:
            with StringIO() as sio:
                inner(sio)
                return sio.getvalue()

        else:
            inner(filename)

    def as_html(self) -> HTML:
        """Render the current map as a static HTML file in IPython.

        !!! warning

            The primary, recommended way to display a map is by
            leaving it as the last line in a cell.

            ```py
            from lonboard import Map

            m = Map(layers=[])
            m
            ```

            This method exists to support environments that are unable to display
            Jupyter Widgets. Some aspects of Lonboard are unavailable with this display
            method. In particular, the map is unable to send any information back to
            Python. So [`selected_index`][lonboard.BaseArrowLayer.selected_index] will
            never be populated, for example.

        Returns:
            IPython HTML object.
        """
        from IPython.display import HTML  # type: ignore

        return HTML(self.to_html())

    @traitlets.default("view_state")
    def _default_initial_view_state(self):
        return compute_view(self.layers)  # type: ignore

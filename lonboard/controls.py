from collections.abc import Sequence
from functools import partial
from typing import Any

import traitlets as t
from ipywidgets import FloatRangeSlider
from ipywidgets.widgets.trait_types import TypedTuple

# Import from source to allow mkdocstrings to link to base class
from ipywidgets.widgets.widget_box import VBox

from lonboard._base import BaseWidget


class MultiRangeSlider(VBox):
    """A widget for multiple ranged sliders.

    This is designed to be used with the
    [DataFilterExtension][lonboard.layer_extension.DataFilterExtension] when you want to
    filter on 2 to 4 columns on the same time.

    If you have only a single filter, use an ipywidgets
    [FloatRangeSlider][ipywidgets.widgets.widget_float.FloatRangeSlider] directly.

    **Example:**

    ```py
    from ipywidgets import FloatRangeSlider

    slider1 = FloatRangeSlider(
        value=(2, 5),
        min=0,
        max=10,
        step=0.1,
        description="First slider: "
    )
    slider2 = FloatRangeSlider(
        value=(30, 40),
        min=0,
        max=50,
        step=1,
        description="Second slider: "
    )
    multi_slider = MultiRangeSlider([slider1, slider2])
    multi_slider
    ```

    Then to propagate updates to a rendered layer, call
    [jsdlink][ipywidgets.widgets.widget_link.jsdlink] to connect the two widgets.

    ```py
    from ipywidgets import jsdlink

    jsdlink(
        (multi_slider, "value"),
        (layer, "filter_range")
    )
    ```

    As you change the slider, the `filter_range` value on the layer class should be
    updated.
    """

    # We use a tuple to force reassignment to update the list
    # This is because list mutations do not get propagated as events
    # https://github.com/jupyter-widgets/ipywidgets/blob/b2531796d414b0970f18050d6819d932417b9953/python/ipywidgets/ipywidgets/widgets/widget_box.py#L52-L54
    value = TypedTuple(trait=TypedTuple(trait=t.Float())).tag(sync=True)

    def __init__(self, children: Sequence[FloatRangeSlider], **kwargs: Any) -> None:
        """Create a new MultiRangeSlider."""
        if len(children) == 1:
            raise ValueError(
                "Expected more than one slider. "
                "For filtering data from a single column, "
                "use a FloatRangeSlider directly.",
            )

        # We manage a list of lists to match what deck.gl expects for the
        # DataFilterExtension
        def callback(change: dict, *, i: int) -> None:
            value = list(self.value)
            value[i] = change["new"]
            self.set_trait("value", value)
            self.send_state("value")

        initial_values = []
        for i, child in enumerate(children):
            func = partial(callback, i=i)
            child.observe(func, "value")
            initial_values.append(child.value)

        super().__init__(children, value=initial_values, **kwargs)


class BaseControl(BaseWidget):
    """A deck.gl or Maplibre Control."""

    position = t.Union(
        [
            t.Unicode("top-left"),
            t.Unicode("top-right"),
            t.Unicode("bottom-left"),
            t.Unicode("bottom-right"),
        ],
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    """Position of the control in the map.

    One of `"top-left"`, `"top-right"`, `"bottom-left"`, or `"bottom-right"`.
    """


class FullscreenControl(BaseControl):
    """A deck.gl FullscreenControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a button to the map
    that allows for toggling fullscreen mode.
    """

    _control_type = t.Unicode("fullscreen").tag(sync=True)


class NavigationControl(BaseControl):
    """A deck.gl NavigationControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add zoom and compass
    buttons to the map.
    """

    _control_type = t.Unicode("navigation").tag(sync=True)

    show_compass = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the compass button.

    Default `True`.
    """

    show_zoom = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the zoom buttons.

    Default `True`.
    """

    visualize_pitch = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable pitch visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `True`.
    """

    visualize_roll = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable roll visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `False`.
    """


class ScaleControl(BaseControl):
    """A deck.gl ScaleControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a scale bar to the
    map.
    """

    _control_type = t.Unicode("scale").tag(sync=True)

    max_width = t.Int(allow_none=True, default_value=None).tag(sync=True)
    """The maximum width of the scale control in pixels.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `100`.
    """

    unit = t.Unicode(allow_none=True, default_value=None).tag(sync=True)
    """The unit of the scale.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    One of `'metric'`, `'imperial'`, or `'nautical'`. Default is `'metric'`.
    """

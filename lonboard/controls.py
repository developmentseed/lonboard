from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

import ipywidgets
import traitlets
from ipywidgets import FloatRangeSlider
from ipywidgets.widgets.trait_types import TypedTuple

# Import from source to allow mkdocstrings to link to base class
from ipywidgets.widgets.widget_box import HBox, VBox

from lonboard.traits import (
    ColorAccessor,
    FloatAccessor,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lonboard._layer import BaseLayer


class MultiRangeSlider(VBox):
    """A widget for multiple ranged sliders.

    This is designed to be used with the
    [DataFilterExtension][lonboard.layer_extension.DataFilterExtension] when you want to
    filter on 2 to 4 columns on the same time.

    If you have only a single filter, use an ipywidgets
    [FloatRangeSlider][ipywidgets.widgets.widget_float.FloatRangeSlider] directly.

    # Example

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
    value = TypedTuple(trait=TypedTuple(trait=traitlets.Float())).tag(sync=True)

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


def _rgb2hex(r: int, g: int, b: int, a: int | None = None) -> str:
    """Convert an RGB(A) color code values to hex."""
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    if a is not None:
        hex_color += f"{a:02x}"
    return hex_color


def _hex2rgb(hex_color: str) -> list[int]:
    """Convert a hex color code to RGB(A)."""
    hex_color = hex_color.lstrip("#")
    rgb_color = []
    if len(hex_color) == 6:
        hex_range = (0, 2, 4)
    if len(hex_color) == 8:
        hex_range = (0, 2, 4, 6)
    for i in hex_range:
        rgb_color.append(int(hex_color[i : i + 2], 16))
    return rgb_color


def _link_rgb_and_hex_traits(
    rgb_object: Any,
    rgb_trait_name: str,
    hex_object: Any,
    hex_trait_name: str,
) -> None:
    """Make links between two objects/traits that hold RBG and hex color codes."""

    def handle_rgb_color_change(change: traitlets.utils.bunch.Bunch) -> None:
        new_color_rgb = change.get("new")[0:3]
        new_color_hex = _rgb2hex(*new_color_rgb)
        hex_object.set_trait(hex_trait_name, new_color_hex)

    rgb_object.observe(handle_rgb_color_change, rgb_trait_name, "change")

    def handle_hex_color_change(change: traitlets.utils.bunch.Bunch) -> None:
        new_color_hex = change.get("new")
        new_color_rgb = _hex2rgb(new_color_hex)
        rgb_object.set_trait(rgb_trait_name, new_color_rgb)

    hex_object.observe(handle_hex_color_change, hex_trait_name, "change")


def _make_visibility_w(layer: BaseLayer) -> ipywidgets.widget:
    """Make a widget to control layer visibility."""
    visibility_w = ipywidgets.Checkbox(
        value=True,
        description="",
        disabled=False,
        indent=False,
    )
    visibility_w.layout = ipywidgets.Layout(width="196px")
    ipywidgets.dlink((layer, "title"), (visibility_w, "description"))
    ipywidgets.link((layer, "visible"), (visibility_w, "value"))
    return visibility_w


def _make_layer_control_item(layer: BaseLayer) -> VBox:
    """Return a VBox to be used by a layer control based on the input layer.

    The VBox will only contain a toggle for the layer's visibility.
    """
    visibility_w = _make_visibility_w(layer)

    # with_layer_controls is False return the visibility widget within a VBox
    # within a HBox to maintain consistency with the layer control item that would be returned
    # if with_layer_controls were True
    return VBox([HBox([visibility_w])])


def _make_layer_control_item_with_settings(layer: BaseLayer) -> VBox:
    """Return a VBox to be used by a layer control based on the input layer.

    The VBox will contain a toggle for the layer's
    visibility and a button that when clicked will display widgets linked to the layers
    traits so they can be modified.
    """
    visibility_w = _make_visibility_w(layer)

    # with_layer_controls is True, make a button that will display the layer props,
    # and widgets for the layer properties. Instead of making the trait controlling
    # widgets in a random order, make lists so we can make the color widgets at the
    # top, followed by the boolean widgets and the number widgets so the layer props
    # display has some sort of order
    color_widgets, bool_widgets, number_widgets = _make_layer_trait_widgets(layer)

    layer_props_title = ipywidgets.HTML(value=f"<b>{layer.title} Properties</b>")
    props_box_layout = ipywidgets.Layout(
        border="solid 3px #EEEEEE",
        width="240px",
        display="none",
    )
    props_widgets = [layer_props_title, *color_widgets, *bool_widgets, *number_widgets]
    layer_props_box = VBox(props_widgets, layout=props_box_layout)

    props_button = ipywidgets.Button(description="", icon="gear")
    props_button.layout.width = "36px"

    def on_props_button_click(_: ipywidgets.widgets.widget_button.Button) -> None:
        if layer_props_box.layout.display != "none":
            layer_props_box.layout.display = "none"
        else:
            layer_props_box.layout.display = "flex"

    props_button.on_click(on_props_button_click)
    return VBox([HBox([visibility_w, props_button]), layer_props_box])


def _trait_name_to_description(trait_name: str) -> str:
    """Make a human readable name from the trait."""
    return trait_name.replace("get_", "").replace("_", " ").title()


## style and layout to keep property wigets consistent
prop_style = {"description_width": "initial"}
prop_layout = ipywidgets.Layout(width="224px")


def _make_color_picker_widget(
    layer: BaseLayer,
    trait_name: str,
) -> ipywidgets.widget:
    trait_description = _trait_name_to_description(trait_name)
    color_trait_value = getattr(layer, trait_name)
    if isinstance(color_trait_value, (list, tuple)) and len(color_trait_value) in [
        3,
        4,
    ]:
        # list or tuples of 3/4 are RGB(a) values
        hex_color = _rgb2hex(*color_trait_value)
    elif color_trait_value is None:
        hex_color = "#000000"
    else:
        return ipywidgets.Label(value=f"{trait_description}: Custom")
    color_picker_w = ipywidgets.ColorPicker(
        description=trait_description,
        layout=prop_layout,
        value=hex_color,
    )
    _link_rgb_and_hex_traits(layer, trait_name, color_picker_w, "value")
    return color_picker_w


def _make_bool_widget(
    layer: BaseLayer,
    trait_name: str,
) -> ipywidgets.widget:
    trait_description = _trait_name_to_description(trait_name)
    bool_w = ipywidgets.Checkbox(
        value=True,
        description=trait_description,
        disabled=False,
        style=prop_style,
        layout=prop_layout,
    )
    ipywidgets.link((layer, trait_name), (bool_w, "value"))
    return bool_w


def _make_float_widget(
    layer: BaseLayer,
    trait_name: str,
    trait: traitlets.TraitType,
) -> ipywidgets.widget:
    trait_description = _trait_name_to_description(trait_name)
    if isinstance(getattr(layer, trait_name), float) is False:
        # not a single value do not make a control widget
        return ipywidgets.Label(value=f"{trait_description}: Custom")
    min_val = None
    if hasattr(trait, "min"):
        min_val = trait.min

    max_val = None
    if hasattr(trait, "max"):
        max_val = trait.max
        if max_val == float("inf"):
            max_val = 999999999999

    if max_val is not None and max_val is not None:
        ## min/max are not None, make a bounded float
        float_w = ipywidgets.BoundedFloatText(
            value=True,
            description=trait_description,
            disabled=False,
            indent=True,
            min=min_val,
            max=max_val,
            style=prop_style,
            layout=prop_layout,
        )
    else:
        ## min/max are None, use normal float, not bounded.
        float_w = ipywidgets.FloatText(
            value=True,
            description=trait_description,
            disabled=False,
            indent=True,
            layout=prop_layout,
        )
    ipywidgets.link((layer, trait_name), (float_w, "value"))
    return float_w


def _make_int_widget(
    layer: BaseLayer,
    trait_name: str,
    trait: traitlets.TraitType,
) -> ipywidgets.widget:
    trait_description = _trait_name_to_description(trait_name)
    if isinstance(getattr(layer, trait_name), int) is False:
        # not a single value, do not make a control widget
        return ipywidgets.Label(value=f"{trait_description}: Custom")
    min_val = None
    if hasattr(trait, "min"):
        min_val = trait.min

    max_val = None
    if hasattr(trait, "max"):
        max_val = trait.max
        if max_val == float("inf"):
            max_val = 999999999999

    if max_val is not None and max_val is not None:
        ## min/max are not None, make a bounded int
        int_w = ipywidgets.BoundedIntText(
            value=True,
            description=trait_description,
            disabled=False,
            indent=True,
            min=min_val,
            max=max_val,
            style=prop_style,
            layout=prop_layout,
        )
    else:
        ## min/max are None, use normal int, not bounded.
        int_w = ipywidgets.IntText(
            value=True,
            description=trait_description,
            disabled=False,
            indent=True,
            style=prop_style,
            layout=prop_layout,
        )
    ipywidgets.link((layer, trait_name), (int_w, "value"))
    return int_w


def _make_layer_trait_widgets(layer: BaseLayer) -> tuple[list, list, list]:
    color_widgets = []
    bool_widgets = []
    number_widgets = []

    for trait_name, trait in layer.traits().items():
        ## Guard against making widgets for protected traits
        if trait_name.startswith("_"):
            continue
        # Guard against making widgets for things we've determined we should not
        # make widgets to change
        if trait_name in ["visible", "selected_index", "title"]:
            continue

        if isinstance(trait, ColorAccessor):
            color_picker_w = _make_color_picker_widget(layer, trait_name)
            color_widgets.append(color_picker_w)
        else:
            if hasattr(layer, trait_name):
                val = getattr(layer, trait_name)

            if val is None:
                # do not create a widget for non color traits that are None
                # becase we dont have a way to set them back to None
                continue

            if isinstance(trait, traitlets.traitlets.Bool):
                bool_w = _make_bool_widget(layer, trait_name)
                bool_widgets.append(bool_w)

            elif isinstance(trait, (FloatAccessor, traitlets.traitlets.Float)):
                float_w = _make_float_widget(layer, trait_name, trait)
                number_widgets.append(float_w)

            elif isinstance(trait, (traitlets.traitlets.Int)):
                int_w = _make_int_widget(layer, trait_name, trait)
                number_widgets.append(int_w)
    return (color_widgets, bool_widgets, number_widgets)

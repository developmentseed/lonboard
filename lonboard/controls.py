from functools import partial
from typing import List, Sequence

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

    def __init__(self, children: Sequence[FloatRangeSlider], **kwargs):
        if len(children) == 1:
            raise ValueError(
                "Expected more than one slider. "
                "For filtering data from a single column, "
                "use a FloatRangeSlider directly."
            )

        # We manage a list of lists to match what deck.gl expects for the
        # DataFilterExtension
        def callback(change, *, i: int):
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


def _rgb2hex(r: int, g: int, b: int) -> str:
    """Converts an RGB color code values to hex."""
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def _hex2rgb(hex_color: str) -> List[int]:
    """Converts a hex color code to RGB."""
    hex_color = hex_color.lstrip("#")
    return list(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _link_rgb_and_hex_traits(
    rgb_object, rgb_trait_name, hex_object, hex_trait_name
) -> None:
    """Makes links between two objects/traits that hold RBG and hex color codes."""

    def handle_RGB_color_change(change: traitlets.utils.bunch.Bunch) -> None:
        new_color_RGB = change.get("new")[0:3]
        new_color_hex = _rgb2hex(*new_color_RGB)
        hex_object.set_trait(hex_trait_name, new_color_hex)

    rgb_object.observe(handle_RGB_color_change, rgb_trait_name, "change")

    def handle_hex_color_change(change: traitlets.utils.bunch.Bunch) -> None:
        new_color_hex = change.get("new")
        new_color_rgb = _hex2rgb(new_color_hex)
        rgb_object.set_trait(rgb_trait_name, new_color_rgb)

    hex_object.observe(handle_hex_color_change, hex_trait_name, "change")


def _make_TOC_item(layer, with_layer_controls: bool = True) -> VBox:
    """
    Returns an ipywidgets VBox to be used by a table of contents based on the input
    Lonboard layer.

    If with_layer_controls is True, the VBox will contain a toggle for the layer's
    visibility and a button that when clicked will display widgets linked to the layers
    traits so they can be modified.

    If with_layer_controls is False, the VBox will only contain a toggle for the layer's
    visibility.
    """
    visibility_w = ipywidgets.Checkbox(
        value=True, description="", disabled=False, indent=False
    )
    visibility_w.layout = ipywidgets.Layout(width="196px")
    ipywidgets.dlink((layer, "title"), (visibility_w, "description"))
    ipywidgets.link((layer, "visible"), (visibility_w, "value"))

    if with_layer_controls is False:
        # with_layer_controls is False return the visibility widget within a VBox
        # within a HBox to maintain consistency with the TOC item that would be returned
        # if with_layer_controls were True
        TOC_item = VBox([HBox([visibility_w])])
    else:
        # with_layer_controls is True, make a button that will display the layer props,
        # and widgets for the layer properties. Instead of making the trait controlling
        # widgets in a random order, make lists so we can make the color widgets at the
        # top, followed by the boolean widgets and the number widgets so the layer props
        # display has some sort of order
        color_widgets = []
        bool_widgets = []
        number_widgets = []

        ## style and layout to keep property wigets consistent
        prop_style = {"description_width": "initial"}
        prop_layout = ipywidgets.Layout(width="224px")
        for trait_name, trait in layer.traits().items():
            ## Guard against making widgets for protected traits
            if trait_name.startswith("_"):
                continue
            # Guard against making widgets for things we've determined we should not
            # make widgets to change
            if trait_name in ["visible", "selected_index", "title"]:
                continue

            ## Make a human readable name from the trait
            trait_description = trait_name.replace("get_", "").replace("_", " ").title()

            if isinstance(trait, ColorAccessor):
                if getattr(layer, trait_name) is not None:
                    hex_color = _rgb2hex(*getattr(layer, trait_name))
                else:
                    hex_color = "#000000"
                color_picker_w = ipywidgets.ColorPicker(
                    description=trait_description, layout=prop_layout, value=hex_color
                )
                _link_rgb_and_hex_traits(layer, trait_name, color_picker_w, "value")
                color_widgets.append(color_picker_w)

            if (
                isinstance(trait, traitlets.traitlets.Bool)
                and getattr(layer, trait_name) is not None
            ):
                bool_w = ipywidgets.Checkbox(
                    value=True,
                    description=trait_description,
                    disabled=False,
                    style=prop_style,
                    layout=prop_layout,
                )
                ipywidgets.link((layer, trait_name), (bool_w, "value"))
                bool_widgets.append(bool_w)

            if (
                isinstance(trait, (FloatAccessor, traitlets.traitlets.Float))
                and getattr(layer, trait_name) is not None
            ):
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
                    ## min/max are None, use normal flaot, not bounded.
                    float_w = ipywidgets.FloatText(
                        value=True,
                        description=trait_description,
                        disabled=False,
                        indent=True,
                        layout=prop_layout,
                    )
                ipywidgets.link((layer, trait_name), (float_w, "value"))
                number_widgets.append(float_w)

            if (
                isinstance(trait, (traitlets.traitlets.Int))
                and getattr(layer, trait_name) is not None
            ):
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
                    float_w = ipywidgets.BoundedIntText(
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
                    float_w = ipywidgets.IntText(
                        value=True,
                        description=trait_description,
                        disabled=False,
                        indent=True,
                        style=prop_style,
                        layout=prop_layout,
                    )
                ipywidgets.link((layer, trait_name), (float_w, "value"))
                number_widgets.append(float_w)

        layer_props_title = ipywidgets.HTML(value=f"<b>{layer.title} Properties</b>")
        props_box_layout = ipywidgets.Layout(
            border="solid 3px #EEEEEE", width="240px", display="none"
        )
        props_widgets = (
            [layer_props_title] + color_widgets + bool_widgets + number_widgets
        )
        layer_props_box = VBox(props_widgets, layout=props_box_layout)

        props_button = ipywidgets.Button(description="", icon="gear")
        props_button.layout.width = "36px"

        def on_props_button_click(_: ipywidgets.widgets.widget_button.Button) -> None:
            if layer_props_box.layout.display != "none":
                layer_props_box.layout.display = "none"
            else:
                layer_props_box.layout.display = "flex"

        props_button.on_click(on_props_button_click)
        TOC_item = VBox([HBox([visibility_w, props_button]), layer_props_box])
    return TOC_item


def make_TOC(lonboard_map, with_layer_controls: bool = True) -> VBox:
    """Function to make create a table of contents (TOC) based on a Lonboard Map.

    The TOC will contain a checkbox for each layer, which controls layer visibility in
    the Lonboard map.

    If `with_layer_controls` is True, each layer in the TOC will also have a settings
    button, which when clicked will expose properties for the layer which can be
    changed.

    If a layer's property is None when the TOC is created,  a widget controling that
    property will not be created.
    """
    toc_items = [
        _make_TOC_item(layer, with_layer_controls) for layer in lonboard_map.layers
    ]
    toc = VBox(toc_items)

    # Observe the map's layers trait, so additions/removals of layers will result in
    #the TOC recreating itself to reflect the map's current state
    def handle_layer_change(change: traitlets.utils.bunch.Bunch) -> None:
        toc_items = [_make_TOC_item(layer) for layer in lonboard_map.layers]
        toc.children = toc_items

    lonboard_map.observe(handle_layer_change, "layers", "change")
    return

from functools import partial
from typing import Sequence

import traitlets
from ipywidgets import FloatRangeSlider
from ipywidgets.widgets.trait_types import TypedTuple

# Import from source to allow mkdocstrings to link to base class
from ipywidgets.widgets.widget_box import VBox


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

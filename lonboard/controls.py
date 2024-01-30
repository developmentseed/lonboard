from functools import partial
from typing import Sequence

import traitlets
from ipywidgets import FloatRangeSlider, VBox
from ipywidgets.widgets.trait_types import TypedTuple


class MultiRangeSlider(VBox):
    """A widget for multiple ranged sliders.

    This is designed to be used with the DataFilterExtension

    If you have only a single filter, use an upstream FloatRangeSlider directly.
    """

    # We use a tuple to force reassignment to update the list
    # This is because list mutations do not get propagated as events
    # https://github.com/jupyter-widgets/ipywidgets/blob/b2531796d414b0970f18050d6819d932417b9953/python/ipywidgets/ipywidgets/widgets/widget_box.py#L52-L54
    value = TypedTuple(trait=TypedTuple(trait=traitlets.Float())).tag(sync=True)

    def __init__(self, children: Sequence[FloatRangeSlider], **kwargs):
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

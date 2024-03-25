from typing import Dict

import traitlets
from anywidget import AnyWidget
from ipywidgets import Widget

msg = """
Unexpected keyword argument: '{provided_trait_name}'.
Check the spelling of your parameters. If you're trying to use layer properties added by
a layer extension, ensure you've passed the extension object into the `extensions`
parameter of the layer.
"""


class BaseWidget(Widget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        # Note: we don't use `class_own_traits()` because some layer props are set on
        # BaseLayer
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(msg.format(provided_trait_name=provided_trait_name))

        super().__init__(**kwargs)


class BaseAnyWidget(AnyWidget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(msg.format(provided_trait_name=provided_trait_name))

        super().__init__(**kwargs)


class BaseExtension(BaseWidget):
    _layer_traits: Dict[str, traitlets.TraitType] = {}
    """Traits from this extension to dynamically assign onto a layer."""

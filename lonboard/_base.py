from typing import Dict

import traitlets
from anywidget import AnyWidget
from ipywidgets import Widget


class BaseWidget(Widget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        # Note: we don't use `class_own_traits()` because some layer props are set on
        # BaseLayer
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(f"unexpected keyword argument '{provided_trait_name}'")

        super().__init__(**kwargs)


class BaseAnyWidget(AnyWidget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(f"unexpected keyword argument '{provided_trait_name}'")

        super().__init__(**kwargs)


class BaseExtension(BaseWidget):
    _layer_traits: Dict[str, traitlets.TraitType] = {}
    """Traits from this extension to dynamically assign onto a layer."""

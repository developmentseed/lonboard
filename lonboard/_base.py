from typing import Any, ClassVar

import traitlets.traitlets as t
from anywidget import AnyWidget
from ipywidgets import Widget

from lonboard._exception_display import ErrorOutput

msg = """
Unexpected keyword argument: '{provided_trait_name}'.
Check the spelling of your parameters. If you're trying to use layer properties added by
a layer extension, ensure you've passed the extension object into the `extensions`
parameter of the layer.
"""


class BaseWidget(Widget):
    _error_output: ErrorOutput

    def __init__(self, **kwargs: Any) -> None:
        # Raise error on unknown keyword name
        # Note: we don't use `class_own_traits()` because some layer props are set on
        # BaseLayer
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs:
            if provided_trait_name not in layer_trait_names:
                raise TypeError(msg.format(provided_trait_name=provided_trait_name))

        self._error_output = ErrorOutput(name=self.__class__.__name__)

        super().__init__(**kwargs)


class BaseAnyWidget(AnyWidget):
    _error_output: ErrorOutput

    def __init__(self, **kwargs: Any) -> None:
        # Raise error on unknown keyword name
        layer_trait_names = self.trait_names()
        for provided_trait_name in kwargs:
            if provided_trait_name not in layer_trait_names:
                raise TypeError(msg.format(provided_trait_name=provided_trait_name))

        self._error_output = ErrorOutput(name=self.__class__.__name__)

        super().__init__(**kwargs)


class BaseExtension(BaseWidget):
    _extension_type: t.Unicode

    _layer_traits: ClassVar[dict[str, t.TraitType]] = {}
    """Traits from this extension to dynamically assign onto a layer."""

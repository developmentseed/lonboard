from anywidget import AnyWidget
from ipywidgets import Widget


class BaseWidget(Widget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        layer_trait_names = self.class_own_traits().keys()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(f"unexpected keyword argument '{provided_trait_name}'")

        super().__init__(**kwargs)


class BaseAnyWidget(AnyWidget):
    def __init__(self, **kwargs):
        # Raise error on unknown keyword name
        layer_trait_names = self.class_own_traits().keys()
        for provided_trait_name in kwargs.keys():
            if provided_trait_name not in layer_trait_names:
                raise TypeError(f"unexpected keyword argument '{provided_trait_name}'")

        super().__init__(**kwargs)

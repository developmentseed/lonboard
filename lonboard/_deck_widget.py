import traitlets
from lonboard._base import BaseWidget

class DeckWidget(BaseWidget):

    props = traitlets.Dict({}).tag(sync=True) # make me a class
    placement = traitlets.Enum(
        values=["top-left", "top-right", "bottom-left", "bottom-right"],
        default_value=None, 
        allow_none=True
    ).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class FullscreenWidget(DeckWidget):
    props = traitlets.Dict({}).tag(sync=True) # make me a class
    placement = traitlets.Enum(
        values=["top-left", "top-right", "bottom-left", "bottom-right"],
        default_value=None, 
        allow_none=True
    ).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
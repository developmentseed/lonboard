import traitlets
from lonboard._base import BaseWidget

class BaseDeckWidget(BaseWidget):

    # props = traitlets.Dict({}).tag(sync=True) # make me a class
    placement = traitlets.Enum(
        values=["top-left", "top-right", "bottom-left", "bottom-right", "fill"],
        default_value=None, 
        allow_none=True
    ).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class FullscreenWidget(BaseDeckWidget):
    _widget_type = traitlets.Unicode("fullscreen").tag(sync=True)

    enter_label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    exit_label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    class_name = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TitleWidget(BaseDeckWidget):

    _widget_type = traitlets.Unicode("title").tag(sync=True)
    title = traitlets.Unicode(allow_none=False).tag(sync=True)
    # position = traitlets.Dict(
    #     key_trait=traitlets.Enum(values=["left", "top", "bottom", "right"]),
    #     value_trait=traitlets.Unicode(),
    #     default_value=None).tag(sync=True)
    font_size = traitlets.Unicode(default_value="32px").tag(sync=True)
    font_style = traitlets.Unicode(default_value="normal").tag(sync=True)
    font_family = traitlets.Unicode(default_value="Helvetica").tag(sync=True)
    font_color = traitlets.Unicode(default_value="rgba(0,0,0,1)").tag(sync=True)
    background_color = traitlets.Unicode(default_value="rgba(255, 255, 255, 0.6)").tag(sync=True)
    outline = traitlets.Unicode(default_value="0px solid rgba(0, 0, 0, 0)").tag(sync=True)
    border_radius = traitlets.Unicode(default_value="5px").tag(sync=True)
    border = traitlets.Unicode(default_value="1px solid rgba(0, 0, 0, 1)").tag(sync=True)
    padding = traitlets.Unicode(default_value="3px").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
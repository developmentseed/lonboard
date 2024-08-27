import traitlets
from lonboard._base import BaseWidget

class BaseDeckWidget(BaseWidget):

    # props = traitlets.Dict({}).tag(sync=True) # make me a class
    placement = traitlets.Enum(
        values=["top-left", "top-right", "bottom-left", "bottom-right", "fill"],
        default_value=None, 
        allow_none=True
    ).tag(sync=True)
    class_name = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)

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

class ZoomWidget(BaseDeckWidget):
    _widget_type = traitlets.Unicode("zoom").tag(sync=True)

    zoom_in_label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    zoom_out_label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    transition_duration = traitlets.Int(default_value=None, allow_none=True).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    class_name = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class CompassWidget(BaseDeckWidget):
    _widget_type = traitlets.Unicode("compass").tag(sync=True)

    label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    transition_duration = traitlets.Int(default_value=None, allow_none=True).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    class_name = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class NorthArrowWidget(BaseDeckWidget):
    _widget_type = traitlets.Unicode("north-arrow").tag(sync=True)

    label = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    transition_duration = traitlets.Int(default_value=None, allow_none=True).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    class_name = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TitleWidget(BaseDeckWidget):

    _widget_type = traitlets.Unicode("title").tag(sync=True)
    title = traitlets.Unicode(allow_none=False).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class LegendWidget(BaseDeckWidget):

    _widget_type = traitlets.Unicode("legend").tag(sync=True)
    title = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    labels = traitlets.List(traitlets.Unicode()).tag(sync=True)
    colors = traitlets.List(traitlets.Unicode()).tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ScaleWidget(BaseDeckWidget):

    _widget_type = traitlets.Unicode("scale").tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    max_width = traitlets.Int(default_value=None, allow_none=True).tag(sync=True)
    use_imperial = traitlets.Bool(default_value=None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SaveImageWidget(BaseDeckWidget):

    _widget_type = traitlets.Unicode("save-image").tag(sync=True)
    style = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
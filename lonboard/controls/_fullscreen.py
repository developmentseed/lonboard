from __future__ import annotations

import traitlets.traitlets as t

from lonboard.controls._base import BaseControl


class FullscreenControl(BaseControl):
    """A deck.gl FullscreenControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a button to the map
    that allows for toggling fullscreen mode.
    """

    _control_type = t.Unicode("fullscreen").tag(sync=True)

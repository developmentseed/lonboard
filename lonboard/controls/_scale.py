from __future__ import annotations

import lonboard.traits as t
from lonboard.controls._base import BaseControl


class ScaleControl(BaseControl):
    """A deck.gl ScaleControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a scale bar to the
    map.
    """

    _control_type = t.Unicode("scale")

    max_width = t.Int(allow_none=True, default_value=None)
    """The maximum width of the scale control in pixels.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `100`.
    """

    unit = t.Unicode(allow_none=True, default_value=None)
    """The unit of the scale.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    One of `'metric'`, `'imperial'`, or `'nautical'`. Default is `'metric'`.
    """

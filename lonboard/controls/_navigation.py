from __future__ import annotations

import lonboard.traits as t
from lonboard.controls._base import BaseControl


class NavigationControl(BaseControl):
    """A deck.gl NavigationControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add zoom and compass
    buttons to the map.
    """

    _control_type = t.Unicode("navigation").tag(sync=True)

    show_compass = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the compass button.

    Default `True`.
    """

    show_zoom = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the zoom buttons.

    Default `True`.
    """

    visualize_pitch = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable pitch visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `True`.
    """

    visualize_roll = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable roll visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `False`.
    """

from __future__ import annotations

import lonboard.traits as t
from lonboard._base import BaseWidget


class BaseControl(BaseWidget):
    """A deck.gl or Maplibre Control."""

    position = t.Union(
        [
            t.Unicode("top-left"),
            t.Unicode("top-right"),
            t.Unicode("bottom-left"),
            t.Unicode("bottom-right"),
        ],
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    """Position of the control in the map.

    One of `"top-left"`, `"top-right"`, `"bottom-left"`, or `"bottom-right"`.
    """

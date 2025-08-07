from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

if TYPE_CHECKING:
    from lonboard.basemap import CartoBasemap


class MapKwargs(TypedDict, total=False):
    """Kwargs to pass into map constructor."""

    height: int | str
    basemap_style: str | CartoBasemap
    parameters: dict[str, Any]
    picking_radius: int
    show_tooltip: bool
    show_side_panel: bool
    use_device_pixels: int | float | bool
    view_state: dict[str, Any]

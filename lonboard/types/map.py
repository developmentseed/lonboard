import sys
from typing import Any, Dict, List, Union

from lonboard.basemap import CartoBasemap
from lonboard._deck_widget import BaseDeckWidget

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class MapKwargs(TypedDict, total=False):
    _initial_view_state: Dict[str, Any]
    _height: int
    show_tooltip: bool
    picking_radius: int
    basemap_style: Union[str, CartoBasemap]
    use_device_pixels: Union[int, float, bool]
    parameters: Dict[str, Any]
    deck_widgets: List[BaseDeckWidget]

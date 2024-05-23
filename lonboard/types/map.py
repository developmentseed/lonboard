import sys
from typing import Any, Dict, Union

from lonboard.basemap import CartoBasemap

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class MapKwargs(TypedDict, total=False):
    _height: int
    basemap_style: Union[str, CartoBasemap]
    parameters: Dict[str, Any]
    picking_radius: int
    show_tooltip: bool
    use_device_pixels: Union[int, float, bool]
    view_state: Dict[str, Any]

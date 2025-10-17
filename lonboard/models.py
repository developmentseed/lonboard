from typing import NamedTuple

from anywidget.experimental import MimeBundleDescriptor
from pydantic import BaseModel, ConfigDict


class ViewState(NamedTuple):
    """State of a view position of a map."""

    longitude: float
    """Longitude at the map center"""

    latitude: float
    """Latitude at the map center."""

    zoom: float
    """Zoom level."""

    pitch: float
    """Pitch angle in degrees. `0` is top-down."""

    bearing: float
    """Bearing angle in degrees. `0` is north."""


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class MapViewState(BaseModel, frozen=True):
    """State of a map view."""

    _repr_mimebundle_ = MimeBundleDescriptor(no_view=True)

    longitude: float
    """Longitude of the map center"""

    latitude: float
    """Latitude of the map center."""

    zoom: float
    """Zoom level."""

    pitch: float | None = None
    """Pitch (tilt) of the map, in degrees. `0` looks top down"""

    bearing: float | None = None
    """Bearing (rotation) of the map, in degrees. `0` is north up"""

    min_zoom: float | None = None
    """Min zoom, default `0`"""

    max_zoom: float | None = None
    """Max zoom, default `20`"""

    min_pitch: float | None = None
    """Min pitch, default `0`"""

    max_pitch: float | None = None
    """Max pitch, default `60`"""

    position: list[float] | None = None
    """Viewport center offsets from lng, lat in meters"""

    near_z: float | None = None
    """The near plane position"""

    far_z: float | None = None
    """The far plane position"""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )

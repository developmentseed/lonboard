from typing import NamedTuple


class ViewState(NamedTuple):
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

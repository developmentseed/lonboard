"""Controls to extend a Map's interactivity."""

from ._base import BaseControl
from ._fullscreen import FullscreenControl
from ._geocoder import (
    GeocoderControl,
    GeocoderFeature,
    GeocoderFeatureCollection,
    GeocoderHandler,
)
from ._navigation import NavigationControl
from ._scale import ScaleControl
from ._slider import MultiRangeSlider

__all__ = [
    "BaseControl",
    "FullscreenControl",
    "GeocoderControl",
    "GeocoderFeature",
    "GeocoderFeatureCollection",
    "GeocoderHandler",
    "MultiRangeSlider",
    "NavigationControl",
    "ScaleControl",
]

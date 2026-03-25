"""Raster support for Lonboard."""

from ._models import EncodedImage
from ._utils import reshape_as_image

__all__ = ["EncodedImage", "reshape_as_image"]

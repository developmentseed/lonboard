from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import sys

    from numpy.typing import NDArray

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer

IMAGE_MIME_TYPES = Literal["image/png", "image/jpeg", "image/webp", "image/avif"]


@dataclass
class EncodedImage:
    """An encoded image in a specific format."""

    data: Buffer
    mime_type: Literal["image/png", "image/jpeg", "image/webp", "image/avif"]


@dataclass
class ImageData:
    """Raw image data as a numpy array."""

    array: NDArray
    width: int
    height: int
    bands: int

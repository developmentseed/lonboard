from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from numpy.typing import NDArray


@dataclass
class EncodedImage:
    """An encoded image in a specific format."""

    data: bytes
    format: Literal["PNG", "JPEG", "WebP"]


@dataclass
class ImageData:
    """Raw image data as a numpy array."""

    array: NDArray
    width: int
    height: int
    bands: int

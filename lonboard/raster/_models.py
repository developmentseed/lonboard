from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


@dataclass
class EncodedImage:
    """An encoded image in a specific format."""

    data: Buffer
    """Image data as a bytes-like object, such as bytes or memoryview."""

    media_type: Literal["image/png", "image/jpeg", "image/webp", "image/avif"]
    """The media type of the image, indicating its format."""

    def __post_init__(self) -> None:
        if self.media_type not in (
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/avif",
        ):
            raise ValueError(
                f"Invalid media_type {self.media_type!r}. Must be one of 'image/png', 'image/jpeg', 'image/webp', or 'image/avif'.",
            )

        if not isinstance(self.data, (bytes, memoryview)):
            # Check if the input is bytes-like by trying to create a memoryview.
            try:
                memoryview(self.data)
            except TypeError as e:
                raise TypeError(
                    f"data must be a bytes-like object such as bytes or memoryview, not {type(self.data).__name__!r}",
                ) from e

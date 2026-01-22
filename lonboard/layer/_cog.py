from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lonboard.layer._base import BaseLayer

if TYPE_CHECKING:
    from async_tiff import TIFF


class COGLayer(BaseLayer):
    """The COGLayer renders imagery from a Cloud-Optimized GeoTIFF."""

    def __init__(
        self,
        tiff: TIFF,
        **kwargs: Any,
    ) -> None:
        pass

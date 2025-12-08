from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import traitlets as t
from affine import Affine

from lonboard.experimental.traits import TextureTrait
from lonboard.layer import BaseLayer

if TYPE_CHECKING:
    import sys
    from typing import Any

    from numpy.typing import NDArray
    from rasterio.io import DatasetReader

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


def load_arr_and_transform(
    src: DatasetReader,
    *,
    downscale: int | None,
) -> tuple[NDArray[np.uint8], Affine]:
    """Load array and transform from rasterio source."""
    if downscale is None:
        return src.read(), src.transform

    # Read overview array from src
    overview_height = int(src.height / downscale)
    overview_width = int(src.width / downscale)
    overview_shape = (src.count, overview_height, overview_width)

    arr: np.ndarray = src.read(out_shape=overview_shape)
    overview_transform = Affine(
        src.transform.a * downscale,  # pixel width
        src.transform.b,  # rotation/skew x
        src.transform.c,  # top-left x
        src.transform.d,  # rotation/skew y
        src.transform.e * downscale,  # pixel height (usually negative)
        src.transform.f,  # top-left y
    )
    return arr, overview_transform


def apply_colormap(
    arr: NDArray[np.uint8],
    cmap: dict[int, tuple[int, int, int] | tuple[int, int, int, int]],
) -> NDArray[np.uint8]:
    """Apply rasterio colormap to single-band array."""
    lut = np.zeros((max(cmap.keys()) + 1, 4), dtype=np.uint8)
    for k, v in cmap.items():
        lut[k] = v

    return lut[arr]


class GeoTiffLayer(BaseLayer):
    """GeoTiffLayer."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)  # type: ignore

    @classmethod
    def from_rasterio(
        cls,
        src: DatasetReader,
        *,
        downscale: int | None = None,
        **kwargs: Any,
    ) -> Self:
        import rasterio.plot

        arr, transform = load_arr_and_transform(src, downscale=downscale)

        if arr.shape[0] == 1 and src.colormap(1) is not None:
            image_arr = apply_colormap(arr[0], src.colormap(1))
        else:
            # swap axes order from (bands, rows, columns) to (rows, columns, bands)
            image_arr = rasterio.plot.reshape_as_image(arr)

        image_height = image_arr.shape[0]
        image_width = image_arr.shape[1]

        return cls(
            source_projection=src.crs.to_wkt(),
            geotransform=transform,
            texture=image_arr,
            width=image_width,
            height=image_height,
            **kwargs,
        )

    _layer_type = t.Unicode("geotiff").tag(sync=True)

    source_projection = t.Unicode().tag(sync=True)
    """The source projection of the GeoTIFF, in Proj4 or WKT format"""

    geotransform = t.List(t.Float()).tag(sync=True)
    """The GeoTIFF geotransform as a list of 6 floats in affine ordering."""

    texture = TextureTrait().tag(sync=True)

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to render the mesh in wireframe mode.

    - Type: `bool`, optional
    - Default: `False`
    """

    width = t.Int().tag(sync=True)
    """The width of the GeoTIFF in pixels."""

    height = t.Int().tag(sync=True)
    """The height of the GeoTIFF in pixels."""

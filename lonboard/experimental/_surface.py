from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pyproj
import traitlets as t
from affine import Affine
from arro3.core import DataType

from lonboard.experimental.traits import MeshAccessor, TextureTrait
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


def rescale_positions_to_image_crs(
    positions: NDArray[np.float32],
    *,
    image_height: int,
    image_width: int,
    transform: Affine,
) -> NDArray[np.float32]:
    # Scale to pixel coordinates
    pixel_coords = positions * np.array([image_width, image_height])
    cols, rows = pixel_coords[:, 0], pixel_coords[:, 1]
    xs, ys = transform * (cols, rows)  # type: ignore (matrix multiplication not typed correctly)
    return np.stack([xs, ys], axis=-1)


class SurfaceLayer(BaseLayer):
    """SurfaceLayer."""

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

        # swap axes order from (bands, rows, columns) to (rows, columns, bands)
        image_arr: np.ndarray = rasterio.plot.reshape_as_image(arr)

        image_height = image_arr.shape[0]
        image_width = image_arr.shape[1]

        positions = np.array(
            [
                [0, 0],  # bottom-left
                [1, 0],  # bottom-right
                [0, 1],  # top-left
                [1, 1],  # top-right
            ],
            dtype=np.float32,
        )

        source_crs_coords = rescale_positions_to_image_crs(
            positions,
            image_height=image_height,
            image_width=image_width,
            transform=transform,
        )

        transformer = pyproj.Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)

        lons, lats = transformer.transform(
            source_crs_coords[:, 0],
            source_crs_coords[:, 1],
        )
        lonlat_coords = np.stack([lons, lats], axis=-1)

        final_positions = np.concatenate(
            [lonlat_coords, np.zeros((lonlat_coords.shape[0], 1), dtype=np.float32)],
            axis=-1,
        )

        triangles = np.array(
            [
                [0, 1, 2],
                [1, 2, 3],
            ],
            dtype=np.uint32,
        )

        tex_coords = np.array(
            [
                [0, 0],  # bottom-left
                [1, 0],  # bottom-right
                [0, 1],  # top-left
                [1, 1],  # top-right
            ],
            dtype=np.float32,
        )

        return cls(
            positions=final_positions,
            triangles=triangles,
            tex_coords=tex_coords,
            texture=image_arr,
            **kwargs,
        )

    _layer_type = t.Unicode("surface").tag(sync=True)

    positions = MeshAccessor(
        list_size=3,
        expected_arrow_type=DataType.list(
            DataType.float32(),
            3,
        ),
    )
    tex_coords = MeshAccessor(
        list_size=2,
        expected_arrow_type=DataType.list(
            DataType.float32(),
            2,
        ),
    )
    triangles = MeshAccessor(
        list_size=3,
        expected_arrow_type=DataType.list(
            DataType.uint32(),
            3,
        ),
    )

    texture = TextureTrait().tag(sync=True)

    wireframe = t.Bool(None, allow_none=True).tag(sync=True)
    """Whether to render the mesh in wireframe mode.

    - Type: `bool`, optional
    - Default: `False`
    """

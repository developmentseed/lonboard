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


def apply_colormap(
    arr: NDArray[np.uint8],
    cmap: dict[int, tuple[int, int, int] | tuple[int, int, int, int]],
) -> NDArray[np.uint8]:
    """Apply rasterio colormap to single-band array."""
    lut = np.zeros((max(cmap.keys()) + 1, 4), dtype=np.uint8)
    for k, v in cmap.items():
        lut[k] = v

    return lut[arr]


def generate_mesh_grid(
    *,
    n_rows: int = 50,
    n_cols: int = 50,
) -> tuple[NDArray[np.float32], NDArray[np.uint32]]:
    """Generate a regular grid mesh with the given number of rows and columns.

    Creates a mesh covering the unit square [0, 1] x [0, 1] divided into
    n_rows x n_cols cells. Each cell is split into two triangles along the diagonal.

    Args:
        n_rows: Number of rows in the grid
        n_cols: Number of columns in the grid

    Returns:
        positions: Array of shape ((n_rows+1) * (n_cols+1), 2) containing vertex positions
                   in normalized image coordinates [0, 1]
        triangles: Array of shape (n_rows * n_cols * 2, 3) containing triangle vertex indices

    """
    # Generate vertex grid
    # We need (n_rows + 1) x (n_cols + 1) vertices to create n_rows x n_cols cells
    x = np.linspace(0, 1, n_cols + 1, dtype=np.float32)
    y = np.linspace(0, 1, n_rows + 1, dtype=np.float32)

    # Create meshgrid and flatten to get all vertex positions
    xx, yy = np.meshgrid(x, y)
    positions = np.stack([xx.ravel(), yy.ravel()], axis=-1)

    # Generate triangle indices
    # For each cell (i, j), we create two triangles:
    # Triangle 1: bottom-left, bottom-right, top-left
    # Triangle 2: bottom-right, top-right, top-left
    triangles = np.empty((n_rows * n_cols * 2, 3), dtype=np.uint32)

    i = 0
    for row in range(n_rows):
        for col in range(n_cols):
            # Vertex indices for the current cell
            bottom_left = row * (n_cols + 1) + col
            bottom_right = bottom_left + 1
            top_left = (row + 1) * (n_cols + 1) + col
            top_right = top_left + 1

            triangles[i] = [bottom_left, bottom_right, top_left]
            triangles[i + 1] = [bottom_right, top_right, top_left]
            i += 2

    triangles_array = np.array(triangles, dtype=np.uint32)

    return positions, triangles_array


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
        mesh_n_rows: int = 50,
        mesh_n_cols: int = 50,
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

        # Generate mesh grid in normalized [0, 1] coordinates
        # These positions serve as texture coordinates
        tex_coords, triangles = generate_mesh_grid(
            n_rows=mesh_n_rows,
            n_cols=mesh_n_cols,
        )

        # Reproject mesh vertices from image CRS to EPSG:4326
        source_crs_coords = rescale_positions_to_image_crs(
            tex_coords,
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

        # Add z-coordinate (elevation), setting to zero as we care about a flat mesh on
        # the map surface
        final_positions = np.concatenate(
            [lonlat_coords, np.zeros((lonlat_coords.shape[0], 1), dtype=np.float32)],
            axis=-1,
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

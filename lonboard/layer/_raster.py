# ruff: noqa: SLF001, ERA001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

import numpy as np
import traitlets.traitlets as t

from lonboard._geoarrow.ops import Bbox, WeightedCentroid
from lonboard.layer._base import BaseLayer
from lonboard.raster import IMAGE_MIME_TYPES, EncodedImage

if TYPE_CHECKING:
    import sys

    from async_geotiff import GeoTIFF
    from async_pmtiles import PMTilesReader
    from numpy.typing import NDArray

    if sys.version_info >= (3, 12):
        from collections.abc import Buffer
    else:
        from typing_extensions import Buffer


# This must be kept in sync with src/model/layer/raster.ts
MSG_KIND = "raster-get-tile-data"

Tile_co = TypeVar("Tile_co", covariant=True)
Tile_contra = TypeVar("Tile_contra", contravariant=True)
T = TypeVar("T")


class FetchTile(Protocol[Tile_co]):
    """Protocol for user-defined fetch_tile function."""

    async def __call__(self, *, x: int, y: int, z: int) -> Tile_co:
        """Fetch a tile asynchronously.

        Args:
            x: The x coordinate of the tile.
            y: The y coordinate of the tile.
            z: The zoom level of the tile.

        Returns:
            A Tile object representing the fetched tile.

        """
        ...


class RenderTile(Protocol[Tile_contra]):
    """Protocol for user-defined render function."""

    def __call__(self, tile: Tile_contra) -> EncodedImage:
        """Render a tile.

        Args:
            tile: A tile object returned by FetchTile.

        Returns:
            An RGBA numpy array representing the rendered tile.

        """
        ...


# class FrontendTileRequest(TypedDict):


def handle_anywidget_dispatch(
    widget: RasterLayer,
    msg: str | list | dict,
    buffers: list[bytes],
) -> None:
    if not isinstance(msg, dict) or msg.get("kind") != MSG_KIND:
        return

    # Schedule the async handler on the event loop
    task = asyncio.create_task(_handle_tile_request(widget, msg, buffers))
    widget._pending_tasks.add(task)
    task.add_done_callback(widget._pending_tasks.discard)


# https://github.com/rasterio/rasterio/blob/2d79e5f3a00e919ecaa9573adba34a78274ce48c/rasterio/plot.py#L227-L241
def reshape_as_image(arr: NDArray) -> NDArray:
    """Return the source array reshaped image axis order.

    This order is expected by image processing and visualization software (matplotlib,
    scikit-image, etc) by swapping the axes order from
    ```
    (bands, rows, columns)
    ```
    to
    ```
    (rows, columns, bands)
    ```
    """
    # swap the axes order from (bands, rows, columns) to (rows, columns, bands)
    return np.transpose(arr, [1, 2, 0])
    # Or, if we use masked arrays in the future:
    # np.ma.transpose(arr, [1, 2, 0])


async def _handle_tile_request(
    widget: RasterLayer,
    msg: dict,
    buffers: list[bytes],
) -> None:
    """Async handler for tile data requests from the frontend."""
    output = widget._error_output

    try:
        if widget.debug:
            output.append_stdout(f"Received tile request: {msg}")

        content = msg["msg"]
        tile = content["tile"]
        index = tile["index"]
        x = index["x"]
        y = index["y"]
        z = index["z"]

        if widget.debug:
            output.append_stdout(f"Fetching tile at x={x}, y={y}, z={z}\n")

        tile = await widget.fetch_tile(x=x, y=y, z=z)
        # TODO: put rendering in thread pool?
        rendered = widget.render(tile)
        buffers = [rendered.data]

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {
                    "type": "encoded-image",
                    "mime_type": rendered.mime_type,
                },
            },
            buffers,
        )
    except Exception:  # noqa: BLE001
        error_msg = traceback.format_exc()
        output.append_stderr(f"Error handling tile request: {error_msg}\n")

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {"error": error_msg},
            },
        )


class RasterLayer(BaseLayer, Generic[T]):
    """The RasterLayer renders raster imagery.

    This layer expects input such as Cloud-Optimized GeoTIFFs (COGs) that can be
    efficiently accessed by internal tiles.
    """

    # Prevent garbage collection of async tasks before they complete.
    # Tasks are removed automatically via add_done_callback when they finish.
    #
    # TODO: ensure JS AbortSignal propagates to cancel these tasks
    _pending_tasks: set[asyncio.Task[None]]

    fetch_tile: FetchTile[T]
    render: RenderTile[T]
    _bounds: Bbox | None
    _center: tuple[float, float] | None

    def __init__(
        self,
        # tms: TileMatrixSet,
        *,
        fetch_tile: FetchTile[T],
        render: RenderTile[T],
        debug: bool = True,
        _bounds: Bbox | None = None,
        _center: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        self._pending_tasks = set()
        self.fetch_tile = fetch_tile
        self.render = render
        self.debug = debug
        self.on_msg(handle_anywidget_dispatch)
        self._bounds = _bounds
        self._center = _center
        super().__init__(**kwargs)  # type: ignore

    @property
    def _bbox(self) -> Bbox:
        # TODO: compute bounds from TMS if not explicitly set
        assert self._bounds is not None
        return self._bounds

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        assert self._center is not None
        return WeightedCentroid(x=self._center[0], y=self._center[1], num_items=100)

    @classmethod
    def from_pmtiles(
        cls,
        reader: PMTilesReader,
    ) -> RasterLayer[Buffer]:
        """Create a RasterLayer from a PMTiles URL."""
        from pmtiles.tile import TileType

        mime_type: IMAGE_MIME_TYPES
        match reader.tile_type:
            case TileType.PNG:
                mime_type = "image/png"
            case TileType.JPEG:
                mime_type = "image/jpeg"
            case TileType.WEBP:
                mime_type = "image/webp"
            case TileType.AVIF:
                mime_type = "image/avif"
            case _:
                raise ValueError(
                    f"PMTiles tile type {reader.tile_type} is not supported by RasterLayer. "
                    "Only raster tile types are supported.",
                )

        async def fetch_tile(
            *,
            x: int,
            y: int,
            z: int,
        ) -> Buffer:
            """Fetch a specific tile from the PMTiles archive."""
            buffer = await reader.get_tile(x=x, y=y, z=z)
            if buffer is None:
                raise ValueError(f"Tile at x={x}, y={y}, z={z} not found in PMTiles.")

            return buffer

        def render(tile: Buffer) -> EncodedImage:
            """Render a tile using the user-provided render function."""
            return EncodedImage(data=tile, mime_type=mime_type)

        return RasterLayer(
            fetch_tile=fetch_tile,
            render=render,
            _bounds=Bbox(*reader.bounds),
            _center=reader.center[:2],
        )

    @classmethod
    def from_async_geotiff(
        cls,
        geotiff: GeoTIFF,
        /,
        *,
        render: RenderTile[Any],
        **kwargs: Any,
        # TODO: can this return type specify RasterLayer[T] where T is the type of the
        # GeoTIFF?
        # Ideally, in a typed context, render should receive the correct tile type
    ) -> RasterLayer[Any]:
        """Create a RasterLayer from a GeoTIFF instance from async-geotiff."""
        from async_geotiff.tms import generate_tms

        tms = generate_tms(geotiff)

        # This should create a closure for fetching tiles from the geotiff. So the user
        # shouldn't have to manually provide a fetch_tile function.

        async def geotiff_fetch_tile(
            x: int,
            y: int,
            z: int,  # noqa: ARG001
        ) -> Any:
            """Fetch a specific tile from the GeoTIFF."""
            # TODO: select correct IFD
            return await geotiff.fetch_tile(x, y)

        return RasterLayer(
            tms=tms,
            fetch_tile=geotiff_fetch_tile,
            render=render,
            **kwargs,
        )  # type: ignore[call-arg]

    _layer_type = t.Unicode("raster").tag(sync=True)

    # TODO: Restore TMS generic tile traversal. For now, for simplicity, we're only rendering standard web mercator tiles.
    # _tms = Dict().tag(sync=True)

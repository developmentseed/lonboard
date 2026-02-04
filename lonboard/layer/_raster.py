# ruff: noqa: SLF001, ERA001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Protocol

import numpy as np
import traitlets.traitlets as t

from lonboard.layer._base import BaseLayer

if TYPE_CHECKING:
    from async_geotiff import GeoTIFF, Tile
    from numpy.typing import NDArray


# This must be kept in sync with src/model/layer/raster.ts
MSG_KIND = "raster-get-tile-data"


class RenderTile(Protocol):
    """Protocol for user-defined render function."""

    def __call__(self, tile: Tile) -> bytes:  # EncodedImage:
        """Render a tile.

        Args:
            tile: A dictionary with tile information.

        Returns:
            An RGBA numpy array representing the rendered tile.

        """
        ...


# TODO: make this a generic Protocol that returns a Tile of a specific type
class FetchTile(Protocol):
    """Protocol for user-defined fetch_tile function."""

    async def __call__(self, x: int, y: int, z: int) -> Tile:
        """Fetch a tile asynchronously.

        Args:
            x: The x coordinate of the tile.
            y: The y coordinate of the tile.
            z: The zoom level of the tile.

        Returns:
            A Tile object representing the fetched tile.

        """
        ...


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
        buffers = [rendered]

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {},  # {"format": rendered.format},
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


class RasterLayer(BaseLayer):
    """The RasterLayer renders raster imagery.

    This layer expects input such as Cloud-Optimized GeoTIFFs (COGs) that can be
    efficiently accessed by internal tiles.
    """

    # Prevent garbage collection of async tasks before they complete.
    # Tasks are removed automatically via add_done_callback when they finish.
    #
    # TODO: ensure JS AbortSignal propagates to cancel these tasks
    _pending_tasks: set[asyncio.Task[None]]

    fetch_tile: FetchTile
    render: RenderTile

    def __init__(
        self,
        # tms: TileMatrixSet,
        *,
        fetch_tile: FetchTile,
        render: RenderTile,
        debug: bool = True,
        **kwargs: Any,
    ) -> None:
        self._pending_tasks = set()
        self.fetch_tile = fetch_tile
        self.render = render
        self.debug = debug
        self.on_msg(handle_anywidget_dispatch)
        super().__init__(**kwargs)  # type: ignore

    @classmethod
    def from_async_geotiff(
        cls,
        geotiff: GeoTIFF,
        /,
        *,
        render: RenderTile,
        **kwargs: Any,
        # TODO: can this return type specify RasterLayer[T] where T is the type of the
        # GeoTIFF?
        # Ideally, in a typed context, render should receive the correct tile type
    ) -> RasterLayer:
        """Create a RasterLayer from a GeoTIFF instance from async-geotiff."""
        from async_geotiff.tms import generate_tms

        tms = generate_tms(geotiff)

        # This should create a closure for fetching tiles from the geotiff. So the user
        # shouldn't have to manually provide a fetch_tile function.

        async def geotiff_fetch_tile(
            x: int,
            y: int,
            z: int,  # noqa: ARG001
        ) -> Tile:
            """Fetch a specific tile from the GeoTIFF."""
            # TODO: select correct IFD
            return await geotiff.fetch_tile(x, y)

        return cls(tms=tms, fetch_tile=geotiff_fetch_tile, render=render, **kwargs)

    _layer_type = t.Unicode("raster").tag(sync=True)

    # TODO: Restore TMS generic tile traversal. For now, for simplicity, we're only rendering standard web mercator tiles.
    # _tms = Dict().tag(sync=True)

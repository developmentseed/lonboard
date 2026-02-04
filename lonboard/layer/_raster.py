# ruff: noqa: SLF001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Protocol

import aiohttp
import numpy as np
import traitlets.traitlets as t
from async_geotiff.tms import generate_tms
from ipywidgets import Output
from traitlets.traitlets import Dict

from lonboard.layer._base import BaseLayer

if TYPE_CHECKING:
    from async_geotiff import GeoTIFF, Tile
    from morecantile.models import TileMatrixSet
    from numpy.typing import NDArray

output = Output()

# This must be kept in sync with src/model/layer/raster.ts
MSG_KIND = "raster-get-tile-data"


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
    # np.ma.transpose(arr, [1, 2, 0]) # noqa: ERA001


async def _handle_tile_request(
    widget: RasterLayer,
    msg: dict,
    buffers: list[bytes],
) -> None:
    """Async handler for tile data requests from the frontend."""
    try:
        with output:
            print(f"Received tile request: {msg}")

        content = msg["msg"]
        tile_id = content["tile_id"]

        # Parse tile coordinates from tile_id (format: "x-y-z")
        # TODO: implement actual tile fetching from widget.tiff
        response = f"tile data for {tile_id}"
        x, y, z = tile_id.split("-")
        x, y, z = int(x), int(y), int(z)

        # TODO: access correct IFD based on zoom level z
        geotiff = widget.geotiff
        tile = await geotiff.fetch_tile(x, y)
        buffer = await tile.decode_async()
        rendered = widget.render(buffer)
        rendered.tobytes("C")

        async with (
            aiohttp.ClientSession() as session,
            session.get("https://example.com") as resp,
        ):
            text = await resp.text()

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": text,
            },
            [],
        )
    except Exception:
        error_msg = traceback.format_exc()
        with output:
            print(f"Error handling tile request: {error_msg}")

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{MSG_KIND}-response",
                "response": {"error": error_msg},
            },
            [],
        )

    # try:
    #     print("handling COG tile request")
    #     content = msg["msg"]
    #     tile_id = content["tile_id"]
    #     tile_x, tile_y, tile_z = tile_id.split("-")
    #     tile_x = int(tile_x)
    #     tile_y = int(tile_y)
    #     tile_z = int(tile_z)

    #     response = "helloworld from init"
    #     return widget.send(
    #         {
    #             "id": msg["id"],
    #             "kind": "anywidget-command-response",
    #             "response": response,
    #         },
    #         [],
    #     )

    #     image_data = widget.reader.tile(int(tile_x), int(tile_y), int(tile_z))

    #     # test.evolve
    #     # rio_tiler.
    #     image_buf = image_data.render(add_mask=True)
    #     buffers = [image_buf]

    #     response = "helloworld from init"
    #     widget.send(
    #         {
    #             "id": msg["id"],
    #             "kind": "anywidget-command-response",
    #             "response": response,
    #         },
    #         buffers,
    #     )
    # except:
    #     response = traceback.format_exc()
    #     widget.send(
    #         {
    #             "id": msg["id"],
    #             "kind": "anywidget-command-response",
    #             "response": response,
    #         },
    #         buffers,
    #     )


class Render(Protocol):
    """Protocol for user-defined render function."""

    def __call__(self, tile: Tile) -> NDArray[np.uint8]:
        """Render a tile.

        Args:
            tile: A dictionary with tile information.

        Returns:
            An RGBA numpy array representing the rendered tile.

        """
        ...


class RasterLayer(BaseLayer):
    """The RasterLayer renders raster imagery.

    This layer expects input such as Cloud-Optimized GeoTIFFs (COGs) that can be
    efficiently accessed by internal tiles.
    """

    # Prevent garbage collection of async tasks before they complete.
    # Tasks are removed automatically via add_done_callback when they finish.
    _pending_tasks: set[asyncio.Task[None]]

    render: Render

    def __init__(
        self,
        tms: TileMatrixSet,
        render: Render,
        **kwargs: Any,
    ) -> None:
        self._pending_tasks = set()
        self.render = render
        self.on_msg(handle_anywidget_dispatch)
        super().__init__(tm=tms, **kwargs)  # type: ignore

    @classmethod
    def from_async_geotiff(
        cls,
        geotiff: GeoTIFF,
        /,
        *,
        render: Render,
        **kwargs: Any,
    ) -> RasterLayer:
        """Create a RasterLayer from a GeoTIFF instance from async-geotiff."""
        tms = generate_tms(geotiff)
        return cls(tms=tms, render=render, **kwargs)

    _layer_type = t.Unicode("cog").tag(sync=True)

    _tms = Dict().tag(sync=True)

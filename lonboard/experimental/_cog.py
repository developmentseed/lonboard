# ruff: noqa: SLF001

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, Protocol

import aiohttp
import numpy as np
import traitlets as t
from async_geotiff.tms import generate_tms
from ipywidgets import Output
from numpy.typing import NDArray
from traitlets.traitlets import Dict
from typing_extensions import Buffer

from lonboard.layer._base import BaseLayer

if TYPE_CHECKING:
    from async_geotiff import GeoTIFF
    from async_tiff import TIFF
    from morecantile.models import TileMatrixSet

output = Output()

# This must be kept in sync with src/model/layer/cog.ts
MSG_KIND = "cog-get-tile-data"


def handle_anywidget_dispatch(
    widget: COGLayer,
    msg: str | list | dict,
    buffers: list[bytes],
) -> None:
    if not isinstance(msg, dict) or msg.get("kind") != MSG_KIND:
        return

    # Schedule the async handler on the event loop
    task = asyncio.create_task(_handle_tile_request(widget, msg, buffers))
    widget._pending_tasks.add(task)
    task.add_done_callback(widget._pending_tasks.discard)


async def _handle_tile_request(
    widget: COGLayer,
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

        tiff = widget.tiff
        tile = await tiff.fetch_tile(x, y, z)
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

    def __call__(self, tile: Buffer) -> NDArray[np.uint8]:
        """Render a tile.

        Args:
            tile: A dictionary with tile information.

        Returns:
            An RGBA numpy array representing the rendered tile.

        """
        ...


class COGLayer(BaseLayer):
    """The COGLayer renders imagery from a Cloud-Optimized GeoTIFF."""

    # Note: not serialized to frontend directly.
    tiff: TIFF

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
        tiff: GeoTIFF,
        /,
        *,
        render: Render,
        **kwargs: Any,
    ) -> COGLayer:
        """Create a COGLayer from a GeoTIFF instance from async-geotiff."""
        tms = generate_tms(tiff)
        return cls(tms=tms, render=render, **kwargs)

    _layer_type = t.Unicode("cog").tag(sync=True)

    _tms = Dict().tag(sync=True)

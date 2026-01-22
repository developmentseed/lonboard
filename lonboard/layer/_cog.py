from __future__ import annotations

from typing import TYPE_CHECKING, Any

import traitlets as t
from ipywidgets import Output

from lonboard.layer._base import BaseLayer

if TYPE_CHECKING:
    from async_tiff import TIFF

output = Output()

# This must be kept in sync with src/model/layer/cog.ts
MSG_KIND = "cog-get-tile-data"


def handle_anywidget_dispatch(
    widget: COGLayer,
    msg: str | list | dict,
    buffers: list[bytes],
) -> None:
    # TODO: wrap in try/except and send error back to frontend

    if not isinstance(msg, dict) or msg.get("kind") != MSG_KIND:
        return

    with output:
        print(f"Received anywidget-command: {msg}")

    response = "helloworld from init"
    widget.send(
        {
            "id": msg["id"],
            "kind": f"{MSG_KIND}-response",
            "response": response,
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
    # except:  # noqa: E722
    #     response = traceback.format_exc()
    #     widget.send(
    #         {
    #             "id": msg["id"],
    #             "kind": "anywidget-command-response",
    #             "response": response,
    #         },
    #         buffers,
    #     )


class COGLayer(BaseLayer):
    """The COGLayer renders imagery from a Cloud-Optimized GeoTIFF."""

    # Note: not serialized to frontend directly.
    tiff: TIFF

    def __init__(
        self,
        tiff: TIFF,
        **kwargs: Any,
    ) -> None:
        self.tiff = tiff
        self.on_msg(handle_anywidget_dispatch)
        super().__init__(**kwargs)  # type: ignore

    _layer_type = t.Unicode("cog").tag(sync=True)

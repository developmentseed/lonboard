from __future__ import annotations

import traceback
from typing import Unpack

from rio_tiler.io.base import BaseReader

# from rio_tiler.io import Reader
# from rio_tiler.models import ImageData
from lonboard.types.layer import BitmapTileLayerKwargs

from .core import BitmapTileLayer

# # path = "/Users/kyle/Downloads/m_1806551_nw_20_030_20221212_20230329.tif"
# path = "/Users/kyle/github/developmentseed/lonboard/m_4007307_sw_18_060_20220803.tif"
# reader = Reader(path)
# reader.geographic_bounds
# reader.tms
# reader.bounds
# test = reader.tile(2601, 3674, 13)
# dir(test)
# # test.mask.all()
# attrs.evolve(test, data=test.data[:3, :, :])
# ImageData()
# image_data = reader.tile(0, 0, 0)

# with open("tmp.png", "wb") as f:
#     f.write(image_data.render())


def handle_anywidget_dispatch(
    widget: RioTilerLayer, msg: str | list | dict, buffers: list[bytes]
) -> None:
    # widget.called += 1
    print(msg)

    if not isinstance(msg, dict) or msg.get("kind") != "anywidget-command":
        return

    try:
        content = msg["msg"]
        tile_id = content["tile_id"]
        tile_x, tile_y, tile_z = tile_id.split("-")
        tile_x = int(tile_x)
        tile_y = int(tile_y)
        tile_z = int(tile_z)

        if tile_z < widget.min_zoom:
            return widget.send(
                {
                    "id": msg["id"],
                    "kind": "anywidget-command-response",
                    "response": {},
                },
                [],
            )

        image_data = widget.reader.tile(int(tile_x), int(tile_y), int(tile_z))

        # test.evolve
        # rio_tiler.
        image_buf = image_data.render(add_mask=True)
        buffers = [image_buf]

        response = "helloworld from init"
        widget.send(
            {
                "id": msg["id"],
                "kind": "anywidget-command-response",
                "response": response,
            },
            buffers,
        )
    except:  # noqa: E722
        response = traceback.format_exc()
        widget.send(
            {
                "id": msg["id"],
                "kind": "anywidget-command-response",
                "response": response,
            },
            buffers,
        )


class RioTilerLayer(BitmapTileLayer):
    reader: BaseReader

    def __init__(
        self,
        reader: BaseReader,
        *,
        min_zoom: int = 10,
        **kwargs: Unpack[BitmapTileLayerKwargs],
    ):
        self.reader = reader
        self.min_zoom = min_zoom

        extent = reader.geographic_bounds
        kwargs["extent"] = tuple(extent)

        self.on_msg(handle_anywidget_dispatch)
        super().__init__(**kwargs)  # type: ignore

    pass

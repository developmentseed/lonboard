"""SPIKE, not for merge: a layer whose data crosses the comm as zarr chunks.

Python serves a virtual zarr store built from an xarray `DataArray`. The browser
reads it through deck.gl-zarr's `ZarrLayer` and styles it on the GPU.
"""

# ruff: noqa

from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any

import numpy as np

import lonboard.traits as t
from lonboard._geoarrow.ops import WeightedCentroid
from lonboard.layer._base import BaseLayer
from lonboard.layer._raster_xarray import (
    WindowLoader,
    _single_level,
    chunk_tile_size,
    level_for,
    spatial_dims,
    wgs84_bounds,
)

if TYPE_CHECKING:
    import xarray as xr

# This must be kept in sync with src/model/layer/zarr.ts
MSG_KIND = "zarr-get"


def _dispatch(widget: ZarrLayer, msg: Any, buffers: list[bytes]) -> None:
    if not isinstance(msg, dict):
        return
    kind = msg.get("kind")
    if kind == f"{MSG_KIND}-cancel":
        task = widget._pending.pop(msg.get("id"), None)
        if task is not None:
            widget.cancelled += 1
            task.cancel()
        return
    if kind != MSG_KIND:
        return
    task_id = msg["id"]
    task = asyncio.create_task(_handle_get(widget, msg))
    widget._pending[task_id] = task
    task.add_done_callback(lambda _: widget._pending.pop(task_id, None))


async def _handle_get(widget: ZarrLayer, msg: dict) -> None:
    key = msg["msg"]["key"]
    byte_range = msg["msg"].get("range")
    reply = {"id": msg["id"], "kind": f"{MSG_KIND}-response"}
    try:
        widget.requests.append(key if byte_range is None else (key, byte_range))
        if widget._proxy is not None:
            chunk = await widget._read_proxy(key, byte_range)
        else:
            chunk = await widget._read_chunk(key)
        if chunk is not None:
            widget.bytes_sent += len(chunk)
        if chunk is None:
            widget.send({**reply, "response": {"type": "missing"}})
        else:
            widget.send({**reply, "response": {"type": "bytes"}}, [chunk])
    except Exception:  # noqa: BLE001
        widget.send({**reply, "response": {"error": traceback.format_exc()}})


class ZarrLayer(BaseLayer):
    """SPIKE: draw an xarray `DataArray` as zarr chunks styled on the GPU."""

    _layer_type = t.Unicode("zarr")

    _metadata = t.Any()
    """`zarr.json` documents of the virtual store, by key."""

    selection = t.Any({})
    """Index of each non-spatial dimension. Changing it fetches again."""

    rescale_min = t.Float(0.0)
    rescale_max = t.Float(1.0)
    """Value range mapped to 0..1 on the GPU. Changing it only redraws."""

    def __init__(
        self,
        *,
        _levels: list[xr.DataArray],
        _metadata: dict,
        _bounds: Any,
        _proxy: Any = None,
        **kwargs: Any,
    ) -> None:
        self._levels = _levels
        self._proxy = _proxy
        self.bytes_sent = 0
        self._pending: dict[str, asyncio.Task] = {}
        self._loader = WindowLoader(
            use_async=all(lvl.chunks is None for lvl in _levels)
        )
        self._bounds = _bounds
        self.requests: list[str] = []
        self.cancelled = 0
        self.on_msg(_dispatch)
        super().__init__(_metadata=_metadata, **kwargs)

    @property
    def _bbox(self) -> Any:
        return self._bounds

    @property
    def _weighted_centroid(self) -> WeightedCentroid:
        b = self._bounds
        return WeightedCentroid(
            x=(b.minx + b.maxx) / 2, y=(b.miny + b.maxy) / 2, num_items=100
        )

    async def _read_chunk(self, key: str) -> bytes | None:
        """Read the chunk a zarr key names: `/<level>/c/<i0>/<i1>/...`."""
        level_path, _, index = key.strip("/").partition("/c/")
        level = self._levels[int(level_path)]
        chunk_shape = self._metadata[f"/{level_path}/zarr.json"]["chunk_grid"][
            "configuration"
        ]["chunk_shape"]
        indices = [int(i) for i in index.split("/")]
        box = {
            dim: slice(i * size, (i + 1) * size)
            for dim, i, size in zip(level.dims, indices, chunk_shape, strict=True)
        }
        window = await self._loader.load(level.isel(box))
        values = np.asarray(window.values, dtype="<f4")
        if values.size == 0:
            return None
        # A zarr chunk is always the full chunk shape; pad edge chunks.
        pad = [(0, size - n) for size, n in zip(chunk_shape, values.shape, strict=True)]
        return np.pad(values, pad, constant_values=np.nan).tobytes()

    @staticmethod
    def from_xarray(
        da: xr.DataArray,
        *,
        crs: Any = None,
        tile_size: int | None = None,
        **kwargs: Any,
    ) -> ZarrLayer:
        levels, transforms, found_crs = _single_level(da, crs, None)
        y_dim, x_dim = spatial_dims(levels[0])
        metadata: dict[str, Any] = {}
        layout = []
        for i, (level, transform) in enumerate(zip(levels, transforms, strict=True)):
            tile_w, tile_h = chunk_tile_size(level, y_dim, x_dim, tile_size)
            # Non-spatial dims get a chunk of 1, so an index travels in the key.
            chunk_shape = [1] * (level.ndim - 2) + [tile_h, tile_w]
            metadata[f"/{i}/zarr.json"] = {
                "zarr_format": 3,
                "node_type": "array",
                "shape": [int(n) for n in level.shape],
                "data_type": "float32",
                "chunk_grid": {
                    "name": "regular",
                    "configuration": {"chunk_shape": chunk_shape},
                },
                "chunk_key_encoding": {
                    "name": "default",
                    "configuration": {"separator": "/"},
                },
                "fill_value": "NaN",
                "codecs": [{"name": "bytes", "configuration": {"endian": "little"}}],
                "dimension_names": [str(d) for d in level.dims],
                "attributes": {},
            }
            layout.append(
                {
                    "asset": str(i),
                    "spatial:transform": [float(v) for v in tuple(transform)[:6]],
                    "spatial:shape": [int(level.sizes[y_dim]), int(level.sizes[x_dim])],
                },
            )
        authority, code = found_crs.to_authority()
        metadata["/zarr.json"] = {
            "zarr_format": 3,
            "node_type": "group",
            "attributes": {
                "spatial:dimensions": [str(y_dim), str(x_dim)],
                "proj:code": f"{authority}:{code}",
                "multiscales": {"layout": layout},
            },
        }
        coarsest = level_for(levels[0], y_dim, x_dim, transforms[0], (512, 512))
        return ZarrLayer(
            _levels=levels,
            _metadata=metadata,
            _bounds=wgs84_bounds(coarsest, found_crs),
            **kwargs,
        )

    async def _read_proxy(self, key: str, byte_range: dict | None) -> bytes | None:
        """Forward a read by key, and optional byte range, to the real store."""
        import obstore

        path = key.strip("/")
        try:
            if byte_range is None:
                result = await obstore.get_async(self._proxy, path)
                return bytes(await result.bytes_async())
            if "suffixLength" in byte_range:
                meta = await obstore.head_async(self._proxy, path)
                start = meta["size"] - byte_range["suffixLength"]
                length = byte_range["suffixLength"]
            else:
                start, length = byte_range["offset"], byte_range["length"]
            return bytes(
                await obstore.get_range_async(
                    self._proxy, path, start=start, length=length
                )
            )
        except FileNotFoundError:
            return None

    @staticmethod
    def from_zarr(store: Any, *, variable: str, **kwargs: Any) -> ZarrLayer:
        """SPIKE: proxy a GeoZarr multiscales group held in an obstore store.

        Python authors the root `zarr.json` it sends: each layout item points at
        the chosen variable's array, and the CRS is sent as PROJJSON.
        """
        import json

        import obstore
        from pyproj import CRS
        from pyproj.transformer import Transformer

        from lonboard._geoarrow.ops import Bbox

        def read_json(path: str) -> dict:
            return json.loads(bytes(obstore.get(store, path).bytes()))

        root = read_json("zarr.json")
        attrs = root["attributes"]
        crs = CRS.from_user_input(attrs["proj:code"])
        metadata: dict[str, Any] = {}
        layout = []
        for item in attrs["multiscales"]["layout"]:
            array_path = f"{item['asset']}/{variable}"
            metadata[f"/{array_path}/zarr.json"] = read_json(f"{array_path}/zarr.json")
            layout.append(
                {
                    "asset": array_path,
                    "spatial:transform": item["spatial:transform"],
                    "spatial:shape": item["spatial:shape"],
                },
            )
        metadata["/zarr.json"] = {
            "zarr_format": 3,
            "node_type": "group",
            "attributes": {
                "spatial:dimensions": attrs["spatial:dimensions"],
                "proj:projjson": crs.to_json_dict(),
                "multiscales": {"layout": layout},
            },
        }
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        bounds = Bbox(*transformer.transform_bounds(*attrs["spatial:bbox"]))
        return ZarrLayer(
            _levels=[],
            _metadata=metadata,
            _bounds=bounds,
            _proxy=store,
            **kwargs,
        )

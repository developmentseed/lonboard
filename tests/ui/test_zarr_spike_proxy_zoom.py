"""SPIKE: the byte-range proxy at a zoom that needs many inner chunks."""

# ruff: noqa

import time
from collections import Counter

import pytest
from obstore.store import HTTPStore
from pyproj import Transformer
from test_utils import setup_map_widget

from lonboard import Map
from lonboard.layer import ZarrLayer

URL = "https://data.eodc.eu/collections/EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/11/16/S2B_MSIL2A_20261116T125959_N0513_R138_T26TMN_20261116T145103.zarr/measurements/reflectance"


@pytest.mark.usefixtures("solara_test")
def test_proxy_many_chunks(page_session):
    layer = ZarrLayer.from_zarr(
        HTTPStore(URL), variable="b04", rescale_min=1000.0, rescale_max=6000.0
    )
    lon, lat = Transformer.from_crs(
        "EPSG:32626", "EPSG:4326", always_xy=True
    ).transform(399960 + 23.5 * 720, 4800000 - 127.5 * 720)
    m = Map(layer, view_state={"longitude": lon, "latitude": lat, "zoom": 12.5})
    m.basemap = None
    t0 = time.time()
    canvas = setup_map_widget(page_session, m)
    t_ready = time.time()
    last, stable_since = -1, time.time()
    while time.time() - t_ready < 90:
        page_session.wait_for_timeout(250)
        if len(layer.requests) != last:
            last, stable_since = len(layer.requests), time.time()
        elif last > 0 and time.time() - stable_since > 3:
            break
    settle = stable_since - t_ready
    levels = Counter(
        r[0].split("/c/")[0] if isinstance(r, tuple) else r.split("/c/")[0]
        for r in layer.requests
    )
    sizes = sorted(
        r[1].get("length", 0) for r in layer.requests if isinstance(r, tuple)
    )
    print(
        "ZOOM requests",
        len(layer.requests),
        "by level",
        dict(levels),
        "bytes %.2f MB" % (layer.bytes_sent / 1e6),
        "settled in %.1fs" % settle,
        "cancelled",
        layer.cancelled,
    )
    print(
        "ZOOM range sizes kB min/median/max",
        sizes[1] // 1000 if len(sizes) > 1 else None,
        sizes[len(sizes) // 2] // 1000,
        sizes[-1] // 1000,
    )
    canvas.screenshot(
        path="/private/tmp/claude-501/-Users-kyle-github-developmentseed-lonboard/f6f634a4-2eb4-4e58-b5e5-721f60b6a2bd/scratchpad/spike-eopf-b04-zoom12.png"
    )

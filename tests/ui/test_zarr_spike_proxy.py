"""SPIKE: Python proxies a real sharded, compressed GeoZarr store's bytes."""

# ruff: noqa

import time

import pytest
from obstore.store import HTTPStore
from pyproj import Transformer
from test_raster import center_pixel
from test_utils import setup_map_widget

from lonboard import Map
from lonboard.layer import ZarrLayer

URL = "https://data.eodc.eu/collections/EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/11/16/S2B_MSIL2A_20261116T125959_N0513_R138_T26TMN_20261116T145103.zarr/measurements/reflectance"


@pytest.mark.usefixtures("solara_test")
def test_proxy_sharded_store(page_session):
    console = []
    page_session.on(
        "console", lambda msg: console.append(f"{msg.type}: {msg.text[:400]}")
    )

    layer = ZarrLayer.from_zarr(
        HTTPStore(URL), variable="b04", rescale_min=1000.0, rescale_max=4000.0
    )
    # Where the scene has data: coarsest-level pixel (row 127, col 23)
    lon, lat = Transformer.from_crs(
        "EPSG:32626", "EPSG:4326", always_xy=True
    ).transform(399960 + 23.5 * 720, 4800000 - 127.5 * 720)
    m = Map(layer, view_state={"longitude": lon, "latitude": lat, "zoom": 9})
    m.basemap = None
    t0 = time.time()
    canvas = setup_map_widget(page_session, m)

    pixel = center_pixel(page_session, canvas)
    for _ in range(120):
        if pixel != (255, 255, 255):
            break
        page_session.wait_for_timeout(250)
        pixel = center_pixel(page_session, canvas)
    page_session.wait_for_timeout(3000)
    pixel = center_pixel(page_session, canvas)
    elapsed = time.time() - t0
    for line in console:
        if "error" in line.lower() and "widget model not found" not in line:
            print("CONSOLE", line)
    print(
        "STEP1 pixel",
        pixel,
        "elapsed %.1fs" % elapsed,
        "requests",
        len(layer.requests),
        "bytes %.2f MB" % (layer.bytes_sent / 1e6),
        "cancelled",
        layer.cancelled,
    )
    for r in layer.requests[:14]:
        print("   REQ", r)
    canvas.screenshot(
        path="/private/tmp/claude-501/-Users-kyle-github-developmentseed-lonboard/f6f634a4-2eb4-4e58-b5e5-721f60b6a2bd/scratchpad/spike-eopf-b04-zoom9.png"
    )
    assert pixel != (255, 255, 255)

    n = len(layer.requests)
    layer.rescale_max = 10000.0
    page_session.wait_for_timeout(1500)
    pixel2 = center_pixel(page_session, canvas)
    print("STEP2 pixel", pixel2, "new requests", len(layer.requests) - n)
    canvas.screenshot(
        path="/private/tmp/claude-501/-Users-kyle-github-developmentseed-lonboard/f6f634a4-2eb4-4e58-b5e5-721f60b6a2bd/scratchpad/spike-eopf-b04-zoom9-restyled.png"
    )
    assert len(layer.requests) == n

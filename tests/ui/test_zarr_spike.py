"""SPIKE: a virtual zarr store over the comm, drawn by deck.gl-zarr's ZarrLayer."""

# ruff: noqa

import numpy as np
import pytest
import xarray as xr
from test_raster import center_pixel
from test_utils import setup_map_widget

from lonboard import Map
from lonboard.layer import ZarrLayer


def _da():
    # Three time steps with constant values 0.0, 0.5 and 1.0
    values = (
        np.zeros((3, 180, 360), "f4") + np.array([0.0, 0.5, 1.0], "f4")[:, None, None]
    )
    return xr.DataArray(
        values,
        coords={
            "time": [0, 1, 2],
            "lat": np.linspace(89.5, -89.5, 180),
            "lon": np.linspace(-179.5, 179.5, 360),
        },
        dims=("time", "lat", "lon"),
    )


def wait_for_red(page_session, canvas, red: int, tries: int = 60):
    pixel = center_pixel(page_session, canvas)
    for _ in range(tries):
        if abs(pixel[0] - red) <= 3 and pixel[1] <= 3 and pixel[2] <= 3:
            break
        page_session.wait_for_timeout(250)
        pixel = center_pixel(page_session, canvas)
    return pixel


@pytest.mark.usefixtures("solara_test")
def test_virtual_zarr_store_renders_and_restyles_without_refetch(page_session):
    console = []
    page_session.on(
        "console", lambda msg: console.append(f"{msg.type}: {msg.text[:300]}")
    )

    layer = ZarrLayer.from_xarray(_da(), selection={"time": 1})
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    m.basemap = None
    canvas = setup_map_widget(page_session, m)

    # 1. It renders: value 0.5 with range 0..1 is half red.
    pixel = wait_for_red(page_session, canvas, 128)
    print("STEP1 pixel", pixel, "requests", layer.requests)
    for line in console:
        if "error" in line.lower():
            print("CONSOLE", line)
    assert abs(pixel[0] - 128) <= 3, pixel
    fetched = list(layer.requests)
    assert fetched == ["/0/c/1/0/0"], fetched

    # 2. A style change redraws with no new data.
    layer.rescale_max = 0.5
    pixel = wait_for_red(page_session, canvas, 255)
    print("STEP2 pixel", pixel, "requests", layer.requests)
    assert abs(pixel[0] - 255) <= 3, pixel
    assert layer.requests == fetched

    # 3. A selection change fetches again, and only the new time step.
    layer.rescale_max = 1.0
    layer.selection = {"time": 2}
    pixel = wait_for_red(page_session, canvas, 255)
    print("STEP3 pixel", pixel, "requests", layer.requests)
    assert abs(pixel[0] - 255) <= 3, pixel
    assert layer.requests == [*fetched, "/0/c/2/0/0"]

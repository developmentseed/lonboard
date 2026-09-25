"""Tests for maps exported with `Map.to_html` and opened directly from disk."""

import io
import time

import geopandas as gpd
from PIL import Image
from playwright.sync_api import Page
from shapely.geometry import box

from lonboard import Map
from lonboard.layer import SolidPolygonLayer

FILL_COLOR = (200, 0, 80)


def _center_pixel(page: Page) -> tuple[int, int, int]:
    canvas_box = page.locator("canvas").first.bounding_box()
    assert canvas_box is not None
    x = canvas_box["x"] + canvas_box["width"] / 2
    y = canvas_box["y"] + canvas_box["height"] / 2
    png = page.screenshot(clip={"x": x, "y": y, "width": 1, "height": 1})
    pixel = Image.open(io.BytesIO(png)).convert("RGB").getpixel((0, 0))
    assert isinstance(pixel, tuple)
    r, g, b = pixel
    return (r, g, b)


def _color_matches(pixel: tuple[int, int, int], expected: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= 2 for a, b in zip(pixel, expected, strict=True))


def _wait_for_center_pixel(
    page: Page,
    expected: tuple[int, int, int],
    timeout: float = 15,
) -> tuple[int, int, int]:
    """Poll the pixel at the center of the map until it matches `expected`."""
    deadline = time.monotonic() + timeout
    pixel = _center_pixel(page)
    while not _color_matches(pixel, expected) and time.monotonic() < deadline:
        page.wait_for_timeout(250)
        pixel = _center_pixel(page)
    return pixel


def test_polygon_fill_renders_when_opened_from_file(page: Page, tmp_path):
    """Polygon fills render in exported HTML opened from a `file://` URL.

    Browsers can't start the earcut blob workers from a `file://` origin, so
    polygon triangulation must fall back to the main thread.

    Regression test for https://github.com/developmentseed/lonboard/issues/1071
    """
    gdf = gpd.GeoDataFrame(geometry=[box(-60, -40, 60, 40)], crs="EPSG:4326")
    layer = SolidPolygonLayer.from_geopandas(gdf, get_fill_color=list(FILL_COLOR))
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 1})
    # No basemap, so the test doesn't depend on fetching tiles
    m.basemap = None
    html_path = tmp_path / "map.html"
    m.to_html(html_path)

    page.goto(html_path.as_uri())
    page.locator("canvas").first.wait_for()

    pixel = _wait_for_center_pixel(page, FILL_COLOR)
    assert _color_matches(pixel, FILL_COLOR), (
        f"Polygon fill never rendered: center pixel is {pixel}, expected {FILL_COLOR}"
    )

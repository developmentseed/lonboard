"""RasterLayer tiles rendered in Python show up on the map."""

import io

import pytest
from PIL import Image
from test_utils import setup_map_widget

from lonboard import Map, RasterLayer

pmtiles_tile = pytest.importorskip("pmtiles.tile")

TILE_COLOR = (200, 0, 80)


def solid_png(color: tuple[int, int, int]) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), color).save(buf, format="PNG")
    return buf.getvalue()


class SolidColorPMTilesReader:
    """A stand-in for `async_pmtiles.PMTilesReader` whose tiles are all one color."""

    tile_type = pmtiles_tile.TileType.PNG
    minzoom = 0
    maxzoom = 6
    bounds = (-180.0, -85.0, 180.0, 85.0)
    center = (0.0, 0.0, 2)

    def __init__(self) -> None:
        self._tile = solid_png(TILE_COLOR)

    async def get_tile(self, x: int, y: int, z: int) -> bytes:  # noqa: ARG002
        return self._tile


def center_pixel(page_session, canvas) -> tuple[int, int, int]:
    canvas_box = canvas.bounding_box()
    assert canvas_box is not None
    png = page_session.screenshot(
        clip={
            "x": canvas_box["x"] + canvas_box["width"] / 2,
            "y": canvas_box["y"] + canvas_box["height"] / 2,
            "width": 1,
            "height": 1,
        },
    )
    pixel = Image.open(io.BytesIO(png)).convert("RGB").getpixel((0, 0))
    assert isinstance(pixel, tuple)
    r, g, b = pixel
    return (r, g, b)


def color_matches(pixel: tuple[int, int, int], expected: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= 2 for a, b in zip(pixel, expected, strict=True))


@pytest.mark.usefixtures("solara_test")
def test_pmtiles_tiles_render(page_session):
    layer = RasterLayer.from_pmtiles(SolidColorPMTilesReader())  # type: ignore[arg-type]
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    # No basemap, so the only thing on the map is the raster tiles
    m.basemap = None
    canvas = setup_map_widget(page_session, m)

    pixel = center_pixel(page_session, canvas)
    for _ in range(60):
        if color_matches(pixel, TILE_COLOR):
            break
        page_session.wait_for_timeout(250)
        pixel = center_pixel(page_session, canvas)

    assert color_matches(pixel, TILE_COLOR), (
        f"Tiles never rendered: center pixel is {pixel}, expected {TILE_COLOR}"
    )

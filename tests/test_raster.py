from __future__ import annotations

import pytest
from affine import Affine
from pyproj import CRS
from traitlets import TraitError

from lonboard import RasterLayer
from lonboard.raster import AffineLevel
from lonboard.traits._raster import meters_per_unit, serialize_affine_levels


class _CrsHolder:
    """Stands in for a widget: `serialize_affine_levels` only reads `_crs`."""

    def __init__(self, crs: str) -> None:
        self._crs = CRS.from_user_input(crs)


def test_affine_level_rejects_nonpositive_size():
    with pytest.raises(ValueError, match="width"):
        AffineLevel(Affine.identity(), width=0, height=1, tile_width=1, tile_height=1)


def test_meters_per_unit():
    assert meters_per_unit(CRS.from_epsg(32612)) == 1.0
    assert meters_per_unit(CRS.from_epsg(4326)) == pytest.approx(111319.4907932736)
    # NAD83 / California zone 3 is in US survey feet
    assert meters_per_unit(CRS.from_epsg(2227)) == 0.30480060960121924


def test_serialize_affine_levels_matches_deck_gl_raster_options():
    level = AffineLevel(
        Affine(10.0, 0.0, 300000.0, 0.0, 10.0, 3990240.0),  # south-up: e > 0
        width=10980,
        height=10980,
        tile_width=512,
        tile_height=256,
    )
    assert serialize_affine_levels([level], _CrsHolder("EPSG:32612")) == [
        {
            "affine": [10.0, 0.0, 300000.0, 0.0, 10.0, 3990240.0],
            "arrayWidth": 10980,
            "arrayHeight": 10980,
            "tileWidth": 512,
            "tileHeight": 256,
            "mpu": 1.0,
        },
    ]


def test_serialize_affine_levels_none():
    assert serialize_affine_levels(None, _CrsHolder("EPSG:4326")) is None


async def _no_tile(x: int, y: int, z: int) -> None:  # noqa: ARG001
    return None


def _no_render(tile: None) -> None:  # noqa: ARG001
    return None


def _level() -> AffineLevel:
    return AffineLevel(
        Affine(1.0, 0.0, -180.0, 0.0, -1.0, 90.0),
        width=360,
        height=180,
        tile_width=512,
        tile_height=512,
    )


def test_affine_levels_state():
    layer = RasterLayer(
        _tile_matrix_set=None,
        _affine_levels=[_level()],
        _crs="EPSG:4326",
        _fetch_tile=_no_tile,
        _render_tile=_no_render,
    )
    state = layer.get_state()
    assert state["_tile_matrix_set"] is None
    assert state["_affine_levels"][0]["arrayWidth"] == 360
    assert state["_affine_levels"][0]["mpu"] == pytest.approx(111319.4907932736)


def test_affine_levels_and_tms_are_exclusive():
    # The check runs before trait validation, so any non-None value stands in
    # for a TileMatrixSet and the test needs no morecantile.
    with pytest.raises(ValueError, match="not both"):
        RasterLayer(
            _tile_matrix_set=object(),  # type: ignore[arg-type]
            _affine_levels=[_level()],
            _crs="EPSG:3857",
            _fetch_tile=_no_tile,
            _render_tile=_no_render,
        )


@pytest.mark.parametrize("bad", [[], [{"affine": [1, 0, 0, 0, 1, 0]}]])
def test_affine_levels_trait_rejects(bad):
    with pytest.raises(TraitError):
        RasterLayer(
            _tile_matrix_set=None,
            _affine_levels=bad,
            _crs="EPSG:4326",
            _fetch_tile=_no_tile,
            _render_tile=_no_render,
        )


def test_from_pmtiles_uses_web_mercator_tiles():
    pmtiles_tile = pytest.importorskip("pmtiles.tile")

    class FakePMTilesReader:
        """Implements the parts of `async_pmtiles.PMTilesReader` that RasterLayer uses."""

        tile_type = pmtiles_tile.TileType.PNG
        minzoom = 2
        maxzoom = 8
        bounds = (-10.0, -20.0, 30.0, 40.0)
        center = (10.0, 10.0, 4)

        async def get_tile(self, x: int, y: int, z: int) -> bytes | None:  # noqa: ARG002
            return None

    layer = RasterLayer.from_pmtiles(FakePMTilesReader())  # type: ignore[arg-type]

    state = layer.get_state()
    # No tile matrix set tells the frontend to request standard XYZ tiles
    assert state["_tile_matrix_set"] is None
    assert layer._crs.to_epsg() == 3857
    assert layer.min_zoom == 2
    assert layer.max_zoom == 8
    assert layer.extent == [-10.0, -20.0, 30.0, 40.0]

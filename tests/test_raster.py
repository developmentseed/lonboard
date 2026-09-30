from __future__ import annotations

import pytest

from lonboard import RasterLayer

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


def test_from_pmtiles_uses_web_mercator_tiles():
    layer = RasterLayer.from_pmtiles(FakePMTilesReader())  # type: ignore[arg-type]

    state = layer.get_state()
    # No tile matrix set tells the frontend to request standard XYZ tiles
    assert state["_tile_matrix_set"] is None
    assert layer._crs.to_epsg() == 3857
    assert layer.min_zoom == 2
    assert layer.max_zoom == 8
    assert layer.extent == [-10.0, -20.0, 30.0, 40.0]

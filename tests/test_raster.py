from __future__ import annotations

import pytest
from affine import Affine
from pyproj import CRS
from traitlets import TraitError

from lonboard import RasterLayer
from lonboard.raster import AffineLevel, AffineTileset, TileMatrixSetAdaptor
from lonboard.traits._raster import meters_per_unit, serialize_tileset


def test_affine_level_rejects_nonpositive_size():
    with pytest.raises(ValueError, match="width"):
        AffineLevel(Affine.identity(), width=0, height=1, tile_width=1, tile_height=1)


def test_meters_per_unit():
    assert meters_per_unit(CRS.from_epsg(32612)) == 1.0
    assert meters_per_unit(CRS.from_epsg(4326)) == pytest.approx(111319.4907932736)
    # NAD83 / California zone 3 is in US survey feet
    assert meters_per_unit(CRS.from_epsg(2227)) == 0.30480060960121924


def test_serialize_tileset_matches_deck_gl_raster_options():
    level = AffineLevel(
        Affine(10.0, 0.0, 300000.0, 0.0, 10.0, 3990240.0),  # south-up: e > 0
        width=10980,
        height=10980,
        tile_width=512,
        tile_height=256,
    )
    tileset = AffineTileset([level], CRS.from_epsg(32612))
    assert serialize_tileset(tileset, None) == [
        {
            "affine": [10.0, 0.0, 300000.0, 0.0, 10.0, 3990240.0],
            "arrayWidth": 10980,
            "arrayHeight": 10980,
            "tileWidth": 512,
            "tileHeight": 256,
            "mpu": 1.0,
        },
    ]


def test_serialize_tileset_none():
    assert serialize_tileset(None, None) is None


def test_affine_tileset_bounds_is_union_of_levels():
    coarse = AffineLevel(Affine(2.0, 0.0, 0.0, 0.0, -2.0, 100.0), 10, 10, 512, 512)
    fine = AffineLevel(Affine(1.0, 0.0, 0.0, 0.0, -1.0, 100.0), 21, 20, 512, 512)
    tileset = AffineTileset([coarse, fine], CRS.from_epsg(3857))
    assert tileset.bounds == (0.0, 80.0, 21.0, 100.0)


def test_affine_tileset_rejects_empty():
    with pytest.raises(ValueError, match="at least one level"):
        AffineTileset([], CRS.from_epsg(3857))


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


def test_tileset_state():
    layer = RasterLayer(
        _tileset=AffineTileset([_level()], CRS.from_epsg(4326)),
        _fetch_tile=_no_tile,
        _render_tile=_no_render,
    )
    state = layer.get_state()
    assert state["_tileset"][0]["arrayWidth"] == 360
    assert state["_tileset"][0]["mpu"] == pytest.approx(111319.4907932736)
    # The CRS comes from the tileset
    assert layer._crs.to_epsg() == 4326


def test_layer_requires_tileset_or_crs():
    with pytest.raises(ValueError, match="_crs"):
        RasterLayer(_tileset=None, _fetch_tile=_no_tile, _render_tile=_no_render)


@pytest.mark.parametrize("bad", [[_level()], {"levels": [_level()]}])
def test_tileset_trait_rejects_non_tilesets(bad):
    with pytest.raises(TraitError):
        RasterLayer(
            _tileset=bad,
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
    # No grid tells the frontend to request standard XYZ tiles
    assert state["_tileset"] is None
    assert layer._crs.to_epsg() == 3857
    assert layer.min_zoom == 2
    assert layer.max_zoom == 8
    assert layer.extent == [-10.0, -20.0, 30.0, 40.0]


def test_tile_matrix_set_adaptor():
    morecantile = pytest.importorskip("morecantile")
    tileset = TileMatrixSetAdaptor(morecantile.tms.get("WebMercatorQuad"))
    assert tileset.crs.to_epsg() == 3857
    assert tileset.bounds == pytest.approx(
        (
            -20037508.342789244,
            -20037508.342789244,
            20037508.342789244,
            20037508.342789244,
        ),
    )
    levels = tileset.levels
    assert len(levels) == 25
    z3 = levels[3]
    assert z3.transform == Affine(
        19567.87924100512,
        0.0,
        -20037508.342789244,
        0.0,
        -19567.87924100512,
        20037508.342789244,
    )
    assert (z3.width, z3.height, z3.tile_width, z3.tile_height) == (
        2048,
        2048,
        256,
        256,
    )


def test_tile_matrix_set_adaptor_bottom_left_origin():
    morecantile = pytest.importorskip("morecantile")
    tms = morecantile.tms.get("WebMercatorQuad")
    matrix = tms.tileMatrices[0].model_copy(update={"cornerOfOrigin": "bottomLeft"})
    level = TileMatrixSetAdaptor(
        tms.model_copy(update={"tileMatrices": [matrix]}),
    ).levels[0]
    assert level.transform.e > 0


class FakeOverview:
    def __init__(self, scale: int) -> None:
        self.transform = Affine(
            10.0 * scale,
            0.0,
            300000.0,
            0.0,
            -10.0 * scale,
            4100040.0,
        )
        self.width = 1024 // scale
        self.height = 1024 // scale
        self.tile_width = 256
        self.tile_height = 256


class FakeGeoTIFF(FakeOverview):
    """Implements the parts of `async_geotiff.GeoTIFF` that from_geotiff uses."""

    crs = CRS.from_epsg(32612)
    bounds = (300000.0, 4089800.0, 310240.0, 4100040.0)

    def __init__(self) -> None:
        super().__init__(1)
        # async-geotiff lists overviews finest first
        self.overviews = [FakeOverview(2), FakeOverview(4)]


def test_from_geotiff_levels_are_coarsest_first():
    layer = RasterLayer.from_geotiff(FakeGeoTIFF(), render_tile=_no_render)  # type: ignore[arg-type]
    levels = layer._tileset.levels
    assert [lvl.transform.a for lvl in levels] == [40.0, 20.0, 10.0]
    assert [lvl.width for lvl in levels] == [256, 512, 1024]
    assert layer._crs.to_epsg() == 32612

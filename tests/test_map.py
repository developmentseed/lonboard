import pytest
from traitlets import TraitError

from lonboard import Map, ScatterplotLayer, SolidPolygonLayer
from lonboard.basemap import MaplibreBasemap


def test_map_fails_with_unexpected_argument():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([1, 2], [3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)

    layer = ScatterplotLayer.from_geopandas(gdf)

    with pytest.raises(TypeError, match="Unexpected keyword argument"):
        _map = Map(layer, unknown_keyword="foo")


def allow_layers_positional_argument():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(gpd.datasets.get_path("nybb"))

    layer = SolidPolygonLayer.from_geopandas(gdf)
    _m = Map([layer])


def allow_single_layer():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(gpd.datasets.get_path("nybb"))

    layer = SolidPolygonLayer.from_geopandas(gdf)
    _m = Map(layer)


def test_map_basemap_non_url():
    with pytest.raises(TraitError, match=r"expected to be a HTTP\(s\) URL"):
        _m = Map([], basemap_style="hello world")


def test_map_default_basemap():
    m = Map([])
    assert isinstance(m.basemap, MaplibreBasemap), (
        "Default basemap should be MaplibreBasemap"
    )

    assert m.basemap.mode == MaplibreBasemap().mode, "Should match default parameters"
    assert m.basemap.style == MaplibreBasemap().style, "Should match default parameters"

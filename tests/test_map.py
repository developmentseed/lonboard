import geopandas as gpd
import pytest
from geodatasets import get_path
from traitlets import TraitError

from lonboard import Map, ScatterplotLayer, SolidPolygonLayer, viz
from lonboard.basemap import MaplibreBasemap
from lonboard.view import FirstPersonView, GlobeView, OrthographicView
from lonboard.view_state import (
    FirstPersonViewState,
    GlobeViewState,
    MapViewState,
    OrthographicViewState,
)


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


def test_view_state_empty_input():
    m = Map([], view_state={})
    assert m.view_state == MapViewState()


def test_view_state_partial_dict():
    view_state = {
        "longitude": -122.45,
        "latitude": 37.8,
    }
    m = Map([], view_state=view_state)
    assert m.view_state == MapViewState(**view_state)


def test_view_state_globe_view_dict():
    view_state = {
        "longitude": -122.45,
        "latitude": 37.8,
        "zoom": 2.0,
    }
    m = Map(
        [],
        view=GlobeView(),
        view_state=view_state,
        basemap=MaplibreBasemap(mode="interleaved"),
    )
    assert m.view_state == GlobeViewState(**view_state)


def test_view_state_globe_view_instance():
    view_state = GlobeViewState(longitude=-122.45, latitude=37.8, zoom=2.0)
    m = Map(
        [],
        view=GlobeView(),
        view_state=view_state,
        basemap=MaplibreBasemap(mode="interleaved"),
    )
    assert m.view_state == view_state


def test_view_state_first_person_dict():
    view_state = {
        "longitude": -122.45,
        "latitude": 37.8,
        "position": [0, 0, 10],
    }
    m = Map([], view=FirstPersonView(), view_state=view_state)
    assert m.view_state == FirstPersonViewState(**view_state)


def test_view_state_orthographic_view_empty():
    view_state = {}
    m = Map([], view=OrthographicView(), view_state=view_state)
    assert m.view_state == OrthographicViewState(**view_state)


def test_set_view_state_map_view_kwargs():
    m = Map([])
    set_state = {"longitude": -100, "latitude": 40, "zoom": 5}
    m.set_view_state(**set_state)
    assert m.view_state == MapViewState(**set_state)


def test_set_view_state_map_view_instance():
    m = Map([])
    set_state = MapViewState(longitude=-100, latitude=40, zoom=5)
    m.set_view_state(set_state)
    assert m.view_state == set_state


def test_set_view_state_partial_update():
    m = Map([], view_state={"longitude": -100, "latitude": 40, "zoom": 5})
    m.set_view_state(latitude=45)
    assert m.view_state == MapViewState(longitude=-100, latitude=45, zoom=5)


def test_globe_view_state_partial_update():
    m = Map(
        [],
        view=GlobeView(),
        view_state={"longitude": -100, "latitude": 40, "zoom": 5},
        basemap=MaplibreBasemap(mode="interleaved"),
    )
    m.set_view_state(latitude=45)
    assert m.view_state == GlobeViewState(longitude=-100, latitude=45, zoom=5)


def test_set_view_state_orbit():
    m = Map(
        [],
        view=FirstPersonView(),
        view_state={"longitude": -100, "latitude": 40},
    )
    new_view_state = FirstPersonViewState(
        longitude=-120,
        latitude=50,
        position=(0, 0, 10),
    )
    m.set_view_state(new_view_state)
    assert m.view_state == new_view_state


def test_map_view_validate_globe_view_basemap():
    with pytest.raises(
        TraitError,
        match=r"GlobeView requires the basemap mode to be 'interleaved'.",
    ):
        Map([], view=GlobeView(), basemap=MaplibreBasemap(mode="overlaid"))

    # Start with interleaved then try to set overlaid
    m = Map([], view=GlobeView(), basemap=MaplibreBasemap(mode="interleaved"))
    with pytest.raises(
        TraitError,
        match=r"GlobeView requires the basemap mode to be 'interleaved'.",
    ):
        m.basemap = MaplibreBasemap(mode="overlaid")

    # Start with overlaid then try to set to GlobeView
    m = Map([], basemap=MaplibreBasemap(mode="overlaid"))
    with pytest.raises(
        TraitError,
        match=r"GlobeView requires the basemap mode to be 'interleaved'.",
    ):
        m.view = GlobeView()


def test_default_view_state_inferred():
    gdf = gpd.read_file(get_path("nybb"))
    m = viz(gdf)
    assert m.view_state == MapViewState(
        longitude=-73.90046557757934,
        latitude=40.67106374683537,
        zoom=9,
    )

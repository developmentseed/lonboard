import geodatasets
import geopandas as gpd
from geoarrow.rust.core import read_pyogrio
from pyogrio.raw import read_arrow

from lonboard import SolidPolygonLayer, viz


def test_viz_wkb_pyarrow():
    path = geodatasets.get_path("naturalearth.land")
    meta, table = read_arrow(path)
    map_ = viz(table)
    assert isinstance(map_.layers[0], SolidPolygonLayer)


def test_viz_reproject():
    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    map_ = viz(gdf)

    # Assert table was reprojected
    first_coord = map_.layers[0].table["geometry"][0][0][0][0]
    expected_coord = -74.05050951794041, 40.56643026026788
    assert (first_coord[0].as_py() - expected_coord[0]) < 0.0001
    assert (first_coord[1].as_py() - expected_coord[1]) < 0.0001


def test_viz_geo_interface():
    class GeoInterfaceHolder:
        def __init__(self, geom) -> None:
            self.geom = geom

        @property
        def __geo_interface__(self):
            return self.geom.__geo_interface__

    gdf = gpd.read_file(geodatasets.get_path("nybb")).to_crs("EPSG:4326")
    geo_interface_obj = GeoInterfaceHolder(gdf.geometry[0])
    map_ = viz(geo_interface_obj)

    assert isinstance(map_.layers[0], SolidPolygonLayer)


def test_viz_geoarrow_rust_table():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    map_ = viz(table)
    assert isinstance(map_.layers[0], SolidPolygonLayer)


def test_viz_geoarrow_rust_array():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    map_ = viz(table.geometry.chunk(0))
    assert isinstance(map_.layers[0], SolidPolygonLayer)


def test_viz_geoarrow_rust_wkb_array():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    arr = table.geometry.chunk(0)
    wkb_arr = arr.to_wkb()
    map_ = viz(wkb_arr)
    assert isinstance(map_.layers[0], SolidPolygonLayer)

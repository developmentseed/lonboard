import geodatasets
import geopandas as gpd
from pyogrio.raw import read_arrow

from lonboard import SolidPolygonLayer, viz


def test_viz_wkb_geoarrow():
    path = geodatasets.get_path("naturalearth.land")
    meta, table = read_arrow(path)
    map_ = viz(table)
    assert isinstance(map_.layers[0], SolidPolygonLayer)


def test_viz_reproject():
    gdf = gpd.read_file(gpd.datasets.get_path("nybb"))
    map_ = viz(gdf)

    # Assert table was reprojected
    first_coord = map_.layers[0].table["geometry"][0][0][0][0]
    expected_coord = -74.05050951794041, 40.56643026026788
    assert (first_coord[0].as_py() - expected_coord[0]) < 0.0001
    assert (first_coord[1].as_py() - expected_coord[1]) < 0.0001

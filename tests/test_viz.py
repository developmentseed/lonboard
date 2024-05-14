from pathlib import Path

import geoarrow.pyarrow as gap
import geodatasets
import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq
import shapely
from geoarrow.rust.core import read_pyogrio
from pyogrio.raw import read_arrow

from lonboard import PathLayer, PolygonLayer, ScatterplotLayer, viz

fixtures_dir = Path(__file__).parent / "fixtures"


def mixed_shapely_geoms():
    pt = shapely.Point(0, 0)
    pt2 = shapely.Point(1, 1)
    line = shapely.LineString([pt, pt2])
    poly = shapely.envelope(shapely.box(0, 0, 1, 1))
    return [pt, line, poly]


def mixed_gdf():
    return gpd.GeoDataFrame({"a": [1, 2, 3]}, geometry=mixed_shapely_geoms())  # type: ignore


class GeoInterfaceHolder:
    """A wrapper class that only exposes __geo_interface__"""

    def __init__(self, geom) -> None:
        self.geom = geom

    @property
    def __geo_interface__(self):
        return self.geom.__geo_interface__


def test_viz_wkb_pyarrow():
    path = geodatasets.get_path("naturalearth.land")
    meta, table = read_arrow(path)
    map_ = viz(table)
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_wkb_mixed_pyarrow():
    table = pq.read_table(fixtures_dir / "monaco_nofilter_noclip_compact.parquet")
    map_ = viz(table)
    assert isinstance(map_.layers[0], PolygonLayer)
    assert isinstance(map_.layers[1], PathLayer)
    assert isinstance(map_.layers[2], ScatterplotLayer)


def test_viz_reproject():
    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    map_ = viz(gdf)

    # Assert table was reprojected
    first_coord = map_.layers[0].table["geometry"][0][0][0][0]
    expected_coord = -74.05050951794041, 40.56643026026788
    assert (first_coord[0].as_py() - expected_coord[0]) < 0.0001
    assert (first_coord[1].as_py() - expected_coord[1]) < 0.0001


def test_viz_geo_interface_geometry():
    gdf = gpd.read_file(geodatasets.get_path("nybb")).to_crs("EPSG:4326")
    geo_interface_obj = GeoInterfaceHolder(gdf.geometry[0])
    map_ = viz(geo_interface_obj)

    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geo_interface_feature_collection():
    gdf = gpd.read_file(geodatasets.get_path("nybb")).to_crs("EPSG:4326")
    geo_interface_obj = GeoInterfaceHolder(gdf)
    map_ = viz(geo_interface_obj)

    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geo_interface_mixed_feature_collection():
    gdf = mixed_gdf()
    geo_interface_obj = GeoInterfaceHolder(gdf)
    map_ = viz(geo_interface_obj)

    assert isinstance(map_.layers[0], PolygonLayer)
    assert isinstance(map_.layers[1], PathLayer)
    assert isinstance(map_.layers[2], ScatterplotLayer)


def test_viz_geopandas_geodataframe():
    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    map_ = viz(gdf)
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_shapely_array():
    gdf = gpd.read_file(geodatasets.get_path("nybb")).to_crs("EPSG:4326")
    map_ = viz(np.array(gdf.geometry))
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_shapely_mixed_array():
    geoms = mixed_shapely_geoms()
    map_ = viz(geoms)

    assert isinstance(map_.layers[0], ScatterplotLayer)
    assert isinstance(map_.layers[1], PathLayer)
    assert isinstance(map_.layers[2], PolygonLayer)


def test_viz_geoarrow_rust_table():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    map_ = viz(table)
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geoarrow_rust_array():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    map_ = viz(table.geometry.chunk(0))
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geoarrow_rust_wkb_array():
    table = read_pyogrio(geodatasets.get_path("naturalearth.land"))
    arr = table.geometry.chunk(0)
    wkb_arr = arr.to_wkb()
    map_ = viz(wkb_arr)
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geoarrow_pyarrow_array_interleaved():
    data = gap.as_geoarrow(
        ["POINT (0 1)", "POINT (2 1)", "POINT (3 1)"],
        coord_type=gap.CoordType.INTERLEAVED,
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], ScatterplotLayer)

    data = gap.as_geoarrow(
        ["LINESTRING (30 10, 10 30, 40 40)"], coord_type=gap.CoordType.INTERLEAVED
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], PathLayer)

    data = gap.as_geoarrow(
        [
            "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
            (
                "POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10),"
                "(20 30, 35 35, 30 20, 20 30))"
            ),
        ],
        coord_type=gap.CoordType.INTERLEAVED,
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], PolygonLayer)


def test_viz_geoarrow_pyarrow_array_separated():
    data = gap.as_geoarrow(
        ["POINT (0 1)", "POINT (2 1)", "POINT (3 1)"], coord_type=gap.CoordType.SEPARATE
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], ScatterplotLayer)

    data = gap.as_geoarrow(
        ["LINESTRING (30 10, 10 30, 40 40)"], coord_type=gap.CoordType.SEPARATE
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], PathLayer)

    data = gap.as_geoarrow(
        [
            "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
            (
                "POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10),"
                "(20 30, 35 35, 30 20, 20 30))"
            ),
        ],
        coord_type=gap.CoordType.SEPARATE,
    )
    map_ = viz(data)
    assert isinstance(map_.layers[0], PolygonLayer)

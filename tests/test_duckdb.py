from tempfile import TemporaryDirectory

import duckdb
import geopandas as gpd
import pytest

from lonboard import PolygonLayer, ScatterplotLayer, SolidPolygonLayer, viz

points_path = gpd.datasets.get_path("naturalearth_cities")


def test_viz_geometry():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "GEOMETRY"
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_wkb_blob():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, ST_AsWKB(geom) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "WKB_BLOB"
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_point_2d():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, CAST(geom as POINT_2D) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "POINT_2D"
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_bbox_2d():
    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(gpd.datasets.get_path("nybb"))
        nybb = nybb.to_crs("EPSG:4326")
        tmp_path = f"{tmpdir}/nybb.shp"
        nybb.to_file(tmp_path)

        con = duckdb.connect()
        sql = f"""
            INSTALL spatial;
            LOAD spatial;
            SELECT * EXCLUDE (geom), ST_Extent(geom) as geom FROM ST_Read("{tmp_path}");
            """
        rel = con.sql(sql)

    assert rel.types[-1] == "BOX_2D"
    m = viz(rel)
    assert isinstance(m.layers[0], PolygonLayer)


def test_layer_geometry():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "GEOMETRY"
    layer = ScatterplotLayer.from_duckdb(rel, con=con)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_wkb_blob():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, ST_AsWKB(geom) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "WKB_BLOB"
    layer = ScatterplotLayer.from_duckdb(rel, con=con)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_point_2d():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, CAST(geom as POINT_2D) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "POINT_2D"
    layer = ScatterplotLayer.from_duckdb(rel)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_bbox_2d():
    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(gpd.datasets.get_path("nybb"))
        tmp_path = f"{tmpdir}/nybb.shp"
        nybb.to_file(tmp_path)

        con = duckdb.connect()
        sql = f"""
            INSTALL spatial;
            LOAD spatial;
            SELECT * EXCLUDE (geom), ST_Extent(geom) as geom FROM ST_Read("{tmp_path}");
            """
        rel = con.sql(sql)

    assert rel.types[-1] == "BOX_2D"
    layer = PolygonLayer.from_duckdb(rel, crs=nybb.crs)
    assert isinstance(layer, PolygonLayer)


def test_solid_polygon_layer_bbox_2d():
    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(gpd.datasets.get_path("nybb"))
        tmp_path = f"{tmpdir}/nybb.shp"
        nybb.to_file(tmp_path)

        con = duckdb.connect()
        sql = f"""
            INSTALL spatial;
            LOAD spatial;
            SELECT * EXCLUDE (geom), ST_Extent(geom) as geom FROM ST_Read("{tmp_path}");
            """
        rel = con.sql(sql)

    assert rel.types[-1] == "BOX_2D"
    layer = SolidPolygonLayer.from_duckdb(rel, crs=nybb.crs)
    assert isinstance(layer, SolidPolygonLayer)


@pytest.mark.skip("Skip because it mutates global state")
def test_create_table_as():
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        CREATE TABLE test AS SELECT * FROM ST_Read("{points_path}");
        """
    duckdb.execute(sql)
    m = viz(duckdb.table("test"))
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_create_table_as_custom_con():
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        CREATE TABLE test AS SELECT * FROM ST_Read("{points_path}");
        """
    con = duckdb.connect()
    con.execute(sql)
    with pytest.raises(ValueError, match="Could not coerce type GEOMETRY to WKB"):
        m = viz(con.table("test"))

    # Succeeds when passing in con object
    m = viz(con.table("test"), con=con)
    assert isinstance(m.layers[0], ScatterplotLayer)

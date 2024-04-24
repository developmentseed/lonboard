import duckdb
import geopandas as gpd
import pytest

from lonboard import PolygonLayer, ScatterplotLayer, viz

points_path = gpd.datasets.get_path("naturalearth_cities")


def test_geometry():
    pass


def test_wkb_blob():
    pass


def test_viz():
    pass


def test_layer():
    pass


@pytest.skip("Skip because it mutates global state")
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


def test_point_2d():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, CAST(geom as POINT_2D) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_bbox_2d():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, ST_Extent(geom) as geom FROM ST_Read("{points_path}");
        """
    rel = con.sql(sql)
    m = viz(rel)
    assert isinstance(m.layers[0], PolygonLayer)

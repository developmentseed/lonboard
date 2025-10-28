from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import duckdb
import geodatasets
import pytest

from lonboard import PolygonLayer, ScatterplotLayer, SolidPolygonLayer, viz

cities_url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_populated_places_simple.zip"
cities_path = Path("ne_110m_populated_places_simple.zip")

if not cities_path.exists():
    urlretrieve(cities_url, "ne_110m_populated_places_simple.zip")  # noqa: S310


cities_gdal_path = f"/vsizip/{cities_path}"


def test_viz_geometry_default_con():
    # For WKB parsing
    pytest.importorskip("shapely")

    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    rel = duckdb.sql(sql)
    assert rel.types[-1] == "GEOMETRY"

    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_geometry():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "GEOMETRY"
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_wkb_blob():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, ST_AsWKB(geom) as geom FROM ST_Read("{cities_gdal_path}");
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
        SELECT name, CAST(geom as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "POINT_2D"
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_bbox_2d():
    gpd = pytest.importorskip("geopandas")

    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(geodatasets.get_path("nybb"))
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
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "GEOMETRY"
    layer = ScatterplotLayer.from_duckdb(rel, con=con)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_wkb_blob():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT name, ST_AsWKB(geom) as geom FROM ST_Read("{cities_gdal_path}");
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
        SELECT name, CAST(geom as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
        """
    rel = con.sql(sql)
    assert rel.types[-1] == "POINT_2D"
    layer = ScatterplotLayer.from_duckdb(rel)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_bbox_2d():
    gpd = pytest.importorskip("geopandas")

    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(geodatasets.get_path("nybb"))
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
        layer = PolygonLayer.from_duckdb(rel, crs=nybb.crs)
        assert isinstance(layer, PolygonLayer)


def test_solid_polygon_layer_bbox_2d():
    gpd = pytest.importorskip("geopandas")

    with TemporaryDirectory() as tmpdir:
        nybb = gpd.read_file(geodatasets.get_path("nybb"))
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
        layer = SolidPolygonLayer.from_duckdb(rel, crs=nybb.crs)
        assert isinstance(layer, SolidPolygonLayer)


@pytest.mark.skip("Skip because it mutates global state")
def test_create_table_as():
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        CREATE TABLE test AS SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    duckdb.execute(sql)
    m = viz(duckdb.table("test"))
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_create_table_as_custom_con():
    # For WKB parsing
    pytest.importorskip("shapely")

    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        CREATE TABLE test AS SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    con = duckdb.connect()
    con.execute(sql)

    m = viz(con.table("test"))
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_geometry_only_column():
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        CREATE TABLE data AS
            SELECT CAST(geom as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
        """
    con.execute(sql)

    _layer = ScatterplotLayer.from_duckdb(con.table("data"), con)

    m = viz(con.table("data"))
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_geometry_only_column_type_geometry():
    # For WKB parsing
    pytest.importorskip("shapely")

    # https://github.com/developmentseed/lonboard/issues/622
    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT geom FROM ST_Read("{cities_gdal_path}");
        """
    query = con.sql(sql)

    # Should create layer without erroring
    _layer = ScatterplotLayer.from_duckdb(query, con)


def test_sanitize_column_name():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT
          * EXCLUDE geom,
          geom as "non_alphanum_colname_()"
        FROM ST_Read("{cities_gdal_path}");
        """
    rel = con.sql(sql)

    with pytest.raises(
        AssertionError,
        match="Expected geometry column name to match regex:",
    ):
        viz(rel)

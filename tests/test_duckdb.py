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

DUCKDB_GE_15 = tuple(int(p) for p in duckdb.__version__.split(".")[:2]) >= (1, 5)


def test_viz_geometry_default_con():
    # For WKB parsing
    pytest.importorskip("shapely")

    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        SELECT * FROM ST_Read("{cities_gdal_path}");
        """
    rel = duckdb.sql(sql)
    # DuckDB 1.5+ parameterizes GEOMETRY with a CRS, e.g. GEOMETRY('EPSG:4326')
    assert str(rel.types[-1]).startswith("GEOMETRY")

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
    # DuckDB 1.5+ parameterizes GEOMETRY with a CRS, e.g. GEOMETRY('EPSG:4326')
    assert str(rel.types[-1]).startswith("GEOMETRY")
    m = viz(rel)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_viz_wkb_blob():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        -- Cast because ST_AsWKB returns plain BLOB (not WKB_BLOB) in DuckDB 1.5+
        SELECT name, ST_AsWKB(geom)::WKB_BLOB as geom FROM ST_Read("{cities_gdal_path}");
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
        -- Cast via plain GEOMETRY: DuckDB 1.5+ can't cast its
        -- CRS-parameterized GEOMETRY directly to POINT_2D
        SELECT name, CAST(geom::GEOMETRY as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
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
    # DuckDB 1.5+ parameterizes GEOMETRY with a CRS, e.g. GEOMETRY('EPSG:4326')
    assert str(rel.types[-1]).startswith("GEOMETRY")
    layer = ScatterplotLayer.from_duckdb(rel, con=con)
    assert isinstance(layer, ScatterplotLayer)


def test_layer_wkb_blob():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = f"""
        INSTALL spatial;
        LOAD spatial;
        -- Cast because ST_AsWKB returns plain BLOB (not WKB_BLOB) in DuckDB 1.5+
        SELECT name, ST_AsWKB(geom)::WKB_BLOB as geom FROM ST_Read("{cities_gdal_path}");
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
        -- Cast via plain GEOMETRY: DuckDB 1.5+ can't cast its
        -- CRS-parameterized GEOMETRY directly to POINT_2D
        SELECT name, CAST(geom::GEOMETRY as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
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
            -- Cast via plain GEOMETRY: DuckDB 1.5+ can't cast its
            -- CRS-parameterized GEOMETRY directly to POINT_2D
            SELECT CAST(geom::GEOMETRY as POINT_2D) as geom FROM ST_Read("{cities_gdal_path}");
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

    if DUCKDB_GE_15:
        # The native Arrow export path doesn't interpolate column names into
        # SQL, so non-alphanumeric geometry column names are supported.
        m = viz(rel)
        assert isinstance(m.layers[0], ScatterplotLayer)
    else:
        with pytest.raises(
            AssertionError,
            match="Expected geometry column name to match regex:",
        ):
            viz(rel)


@pytest.mark.skipif(not DUCKDB_GE_15, reason="GEOMETRY CRS requires duckdb>=1.5")
def test_geometry_crs_used_automatically():
    # For WKB parsing
    pytest.importorskip("shapely")

    con = duckdb.connect()
    # EPSG:3857 coordinates of approximately (lon=1, lat=1)
    sql = """
        INSTALL spatial;
        LOAD spatial;
        SELECT
            'a' as name,
            ST_Point(111319.49079327357, 111325.1428663851)::GEOMETRY('EPSG:3857')
                as geom;
        """
    rel = con.sql(sql)
    m = viz(rel)

    # The 3857 CRS must be picked up from the column type and the data
    # reprojected, so the map centers near (1, 1), not at web-mercator meters.
    assert abs(m.view_state.longitude - 1) < 1e-3
    assert abs(m.view_state.latitude - 1) < 1e-3


@pytest.mark.skipif(not DUCKDB_GE_15, reason="GEOMETRY CRS requires duckdb>=1.5")
def test_crs_param_redundant_with_column_crs_warns():
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = """
        INSTALL spatial;
        LOAD spatial;
        SELECT ST_Point(1.0, 2.0)::GEOMETRY('EPSG:4326') as geom;
        """
    rel = con.sql(sql)

    with pytest.warns(UserWarning, match="no longer needed"):
        ScatterplotLayer.from_duckdb(rel, con=con, crs="EPSG:4326")


@pytest.mark.skipif(not DUCKDB_GE_15, reason="GEOMETRY CRS requires duckdb>=1.5")
def test_crs_param_conflicts_with_column_crs_raises():
    pytest.importorskip("shapely")

    con = duckdb.connect()
    sql = """
        INSTALL spatial;
        LOAD spatial;
        SELECT ST_Point(1.0, 2.0)::GEOMETRY('EPSG:4326') as geom;
        """
    rel = con.sql(sql)

    with pytest.raises(ValueError, match="does not match"):
        ScatterplotLayer.from_duckdb(rel, con=con, crs="EPSG:3857")


@pytest.mark.skipif(not DUCKDB_GE_15, reason="exercises duckdb>=1.5 export path")
def test_crs_param_applied_when_column_has_no_crs():
    import json
    import warnings

    from lonboard._geoarrow._duckdb import from_duckdb

    con = duckdb.connect()
    # Plain GEOMETRY: no CRS encoded in the type
    sql = """
        INSTALL spatial;
        LOAD spatial;
        SELECT ST_Point(1.0, 2.0) as geom;
        """
    rel = con.sql(sql)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        table = from_duckdb(rel, crs="EPSG:3857")

    # The parameter must be applied without the "no longer needed" warning
    assert not any("no longer needed" in str(w.message) for w in caught)
    field = table.schema.field(0)
    ext_meta = json.loads(field.metadata[b"ARROW:extension:metadata"])
    assert ext_meta["crs"]["id"] == {"authority": "EPSG", "code": 3857}

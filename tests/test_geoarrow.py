import json
from tempfile import NamedTemporaryFile

import geodatasets
import geopandas as gpd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import shapely
from arro3.core import ChunkedArray, Table
from geoarrow.rust.core import GeoArray, geometry, points
from pyproj import CRS

from lonboard import ScatterplotLayer, SolidPolygonLayer, viz
from lonboard._constants import OGC_84
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.ops.reproject import reproject_table
from lonboard._utils import get_geometry_column_index


def test_geopandas_table_reprojection():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    layer = SolidPolygonLayer.from_geopandas(gdf)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"],
    )["crs"]
    assert (
        CRS.from_json(
            reprojected_crs_str,
        )
        == OGC_84
    ), "layer should be reprojected to WGS84"


def test_geoarrow_table_reprojection():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    table = geopandas_to_geoarrow(gdf)

    geom_col_idx = get_geometry_column_index(table.schema)
    assert geom_col_idx is not None, "geom column should exist"

    geom_field = table.schema.field(geom_col_idx)
    assert b"ARROW:extension:metadata" in geom_field.metadata, (
        "Metadata key should exist"
    )

    crs_dict = json.loads(geom_field.metadata[b"ARROW:extension:metadata"])["crs"]
    assert gdf.crs == CRS.from_json_dict(
        crs_dict,
    ), "round trip crs should match gdf crs"

    layer = SolidPolygonLayer(table=table)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"],
    )["crs"]
    assert (
        CRS.from_json(
            reprojected_crs_str,
        )
        == OGC_84
    ), "layer should be reprojected to WGS84"


def test_reproject_sliced_array():
    """See https://github.com/developmentseed/lonboard/issues/390"""
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    table = geopandas_to_geoarrow(gdf)
    sliced_table = Table.from_arrow(pa.table(table).slice(2))
    # This should work even with a sliced array.
    _reprojected = reproject_table(sliced_table, to_crs=OGC_84)


def test_geoparquet_metadata():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))

    with NamedTemporaryFile("+wb", suffix=".parquet") as f:
        gdf.to_parquet(f)
        table = pq.read_table(f)

    _layer = SolidPolygonLayer(table=table)


def test_read_geometry_type():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    arr = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb"))
    geometry_arr = arr.cast(geometry())

    # Pass to viz
    out = viz(geometry_arr)
    assert isinstance(out.layers[0], ScatterplotLayer)

    # Pass to layer directly
    _layer = ScatterplotLayer(geometry_arr)


def test_mixed_point_multipoint_types_layer_constructor():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    geometry_arr1 = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb")).cast(
        geometry(),
    )

    multipoints = shapely.multipoints([[1, 2], [3, 4], [5, 6]])
    geometry_arr2 = GeoArray.from_arrow(
        gpd.GeoSeries(multipoints).to_arrow("wkb"),
    ).cast(geometry())

    ca = ChunkedArray([geometry_arr1, geometry_arr2])

    # Pass to viz
    out = viz(ca)
    assert isinstance(out.layers[0], ScatterplotLayer)
    assert len(out.layers) == 1

    # Pass to layer directly
    _layer = ScatterplotLayer(ca)


def test_read_geometry_type_from_table():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    arr = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb"))
    geometry_arr = arr.cast(geometry())
    table = Table.from_arrays([geometry_arr], names=["geometry"])

    # Pass to viz
    out = viz(table)
    assert isinstance(out.layers[0], ScatterplotLayer)

    # Pass to layer directly
    _layer = ScatterplotLayer(table)


def test_geoarrow_geometry_with_crs():
    coords = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float64)

    crs = "EPSG:4326"
    geometry_array = points(coords, crs=crs).cast(geometry(crs=crs))
    m = viz(geometry_array)
    assert isinstance(m.layers[0], ScatterplotLayer)

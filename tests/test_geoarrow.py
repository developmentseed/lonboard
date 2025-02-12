import json
from tempfile import NamedTemporaryFile

import geodatasets
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from arro3.core import Table
from pyproj import CRS

from lonboard import SolidPolygonLayer
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

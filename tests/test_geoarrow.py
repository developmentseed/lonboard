import json

import geodatasets
import geopandas as gpd
from pyproj import CRS

from lonboard import SolidPolygonLayer
from lonboard._constants import OGC_84
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._utils import get_geometry_column_index


def test_geopandas_table_reprojection():
    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    layer = SolidPolygonLayer.from_geopandas(gdf)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"]
    )["crs"]
    assert OGC_84 == CRS.from_json(
        reprojected_crs_str
    ), "layer should be reprojected to WGS84"


def test_geoarrow_table_reprojection():
    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    table = geopandas_to_geoarrow(gdf)

    geom_col_idx = get_geometry_column_index(table.schema)
    assert geom_col_idx is not None, "geom column should exist"

    geom_field = table.schema.field(geom_col_idx)
    assert (
        b"ARROW:extension:metadata" in geom_field.metadata
    ), "Metadata key should exist"

    crs_str = json.loads(geom_field.metadata[b"ARROW:extension:metadata"])["crs"]
    assert gdf.crs == CRS.from_json(crs_str), "round trip crs should match gdf crs"

    layer = SolidPolygonLayer(table=table)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"]
    )["crs"]
    assert OGC_84 == CRS.from_json(
        reprojected_crs_str
    ), "layer should be reprojected to WGS84"

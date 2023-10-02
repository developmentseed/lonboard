"""High-level, super-simple API for visualizing GeoDataFrames
"""

# TODO: avoid geopandas hard dependency
import geopandas as gpd

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.layer import LineStringLayer, PointLayer, PolygonLayer
from lonboard.widget import Map


def viz(data: gpd.GeoDataFrame, **kwargs) -> Map:
    table = geopandas_to_geoarrow(data)
    geometry_ext_type = table.schema.field("geometry").metadata.get(
        b"ARROW:extension:name"
    )

    if geometry_ext_type == "geoarrow.point":
        layer = PointLayer.from_pyarrow(table, **kwargs)
        return Map(layers=[layer])
    elif geometry_ext_type == "geoarrow.linestring":
        layer = LineStringLayer.from_pyarrow(table, **kwargs)
        return Map(layers=[layer])
    elif geometry_ext_type == "geoarrow.point":
        layer = PolygonLayer.from_pyarrow(table, **kwargs)
        return Map(layers=[layer])

    raise ValueError(
        "Only point, linestring, and polygon geometry types currently supported."
    )

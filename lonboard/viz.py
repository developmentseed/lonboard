"""High-level, super-simple API for visualizing GeoDataFrames
"""

# TODO: avoid geopandas hard dependency
import geopandas as gpd

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.layer import BaseLayer, PathLayer, ScatterplotLayer, SolidPolygonLayer


def viz(data: gpd.GeoDataFrame, **kwargs) -> BaseLayer:
    table = geopandas_to_geoarrow(data)
    geometry_ext_type = table.schema.field("geometry").metadata.get(
        b"ARROW:extension:name"
    )

    if geometry_ext_type == "geoarrow.point":
        return ScatterplotLayer.from_pyarrow(table, **kwargs)

    elif geometry_ext_type == "geoarrow.linestring":
        return PathLayer.from_pyarrow(table, **kwargs)

    elif geometry_ext_type == "geoarrow.point":
        return SolidPolygonLayer.from_pyarrow(table, **kwargs)

    raise ValueError(
        "Only point, linestring, and polygon geometry types currently supported."
    )

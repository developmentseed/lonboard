from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pyarrow as pa
import traitlets
from anywidget import AnyWidget

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.serialization import (
    COLOR_SERIALIZATION,
    FLOAT_SERIALIZATION,
    serialize_table_to_parquet,
)

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"


class BaseLayer(AnyWidget):
    pass
    # Note: this _repr_keys is useful if subclassing directly from ipywidgets.Widget, as
    # that will try to print all the included keys by default
    # def _repr_keys(self):
    #     # Exclude the table_buffer from the repr; otherwise printing the buffer will
    #     # often crash the kernel.

    #     # TODO: also exclude keys when numpy array?
    #     exclude_keys = {"table_buffer"}
    #     for key in super()._repr_keys():
    #         if key in exclude_keys:
    #             continue

    #         yield key


# NOTE: I found that traitlets.Union was **extremely** slow to validate a numpy ndarray.
# Like 6 seconds just for an isinstance check.
#
# SCALAR_COLOR_TRAIT = traitlets.List(
#         traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
# )
# VECTORIZED_COLOR_TRAIT = traitlets.Any()
# COLOR_TRAIT = traitlets.Union([VECTORIZED_COLOR_TRAIT,
#     SCALAR_COLOR_TRAIT]).tag(sync=True)


class ScatterplotLayer(BaseLayer):
    _esm = bundler_output_dir / "scatterplot-layer.js"

    _layer_type = traitlets.Unicode("scatterplot").tag(sync=True)

    table_buffer = traitlets.Bytes().tag(sync=True)
    radius_units = traitlets.Unicode("meters", allow_none=True).tag(sync=True)
    radius_scale = traitlets.Float(allow_none=True).tag(sync=True)
    radius_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    radius_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    line_width_units = traitlets.Float(allow_none=True).tag(sync=True)
    line_width_scale = traitlets.Float(allow_none=True).tag(sync=True)
    line_width_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    line_width_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    stroked = traitlets.Bool(allow_none=True).tag(sync=True)
    filled = traitlets.Bool(allow_none=True).tag(sync=True)
    billboard = traitlets.Bool(allow_none=True).tag(sync=True)
    antialiasing = traitlets.Bool(allow_none=True).tag(sync=True)
    get_radius = traitlets.Any().tag(sync=True, **FLOAT_SERIALIZATION)
    get_fill_color = traitlets.Any().tag(sync=True, **COLOR_SERIALIZATION)
    get_line_color = traitlets.Any().tag(sync=True, **COLOR_SERIALIZATION)
    get_line_width = traitlets.Any().tag(sync=True, **FLOAT_SERIALIZATION)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> ScatterplotLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.point"
        ), "Only Point geometries are currently supported by this layer."

        table_buffer = serialize_table_to_parquet(table)
        return cls(table_buffer=table_buffer, **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> ScatterplotLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)


class PathLayer(BaseLayer):
    _esm = bundler_output_dir / "path-layer.js"
    _layer_type = traitlets.Unicode("path").tag(sync=True)

    table_buffer = traitlets.Bytes().tag(sync=True)

    width_units = traitlets.Unicode(allow_none=True).tag(sync=True)
    width_scale = traitlets.Float(allow_none=True).tag(sync=True)
    width_min_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    width_max_pixels = traitlets.Float(allow_none=True).tag(sync=True)
    joint_rounded = traitlets.Bool(allow_none=True).tag(sync=True)
    cap_rounded = traitlets.Bool(allow_none=True).tag(sync=True)
    miter_limit = traitlets.Int(allow_none=True).tag(sync=True)
    billboard = traitlets.Bool(allow_none=True).tag(sync=True)
    get_color = traitlets.Any().tag(sync=True, **COLOR_SERIALIZATION)
    get_width = traitlets.Any().tag(sync=True, **FLOAT_SERIALIZATION)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> PathLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.linestring"
        ), "Only LineString geometries are currently supported by this layer."

        table_buffer = serialize_table_to_parquet(table)
        return cls(table_buffer=table_buffer, **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> PathLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)


class SolidPolygonLayer(BaseLayer):
    _esm = bundler_output_dir / "solid-polygon-layer.js"
    _layer_type = traitlets.Unicode("solid-polygon").tag(sync=True)

    table_buffer = traitlets.Bytes().tag(sync=True)

    filled = traitlets.Bool(allow_none=True).tag(sync=True)
    extruded = traitlets.Bool(allow_none=True).tag(sync=True)
    wireframe = traitlets.Bool(allow_none=True).tag(sync=True)
    elevation_scale = traitlets.Float(allow_none=True).tag(sync=True)
    get_elevation = traitlets.Any().tag(sync=True, **FLOAT_SERIALIZATION)
    get_fill_color = traitlets.Any().tag(sync=True, **COLOR_SERIALIZATION)
    get_line_color = traitlets.Any().tag(sync=True, **COLOR_SERIALIZATION)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> SolidPolygonLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.polygon"
        ), "Only Polygon geometries are currently supported by this layer."

        table_buffer = serialize_table_to_parquet(table)
        return cls(table_buffer=table_buffer, **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> SolidPolygonLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)

from __future__ import annotations

from io import BytesIO

import geopandas as gpd
import ipywidgets
import pyarrow as pa
import pyarrow.feather as feather
import traitlets

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow


class BaseLayer(ipywidgets.Widget):
    def _repr_keys(self):
        # Exclude the table_buffer from the repr; otherwise printing the buffer will
        # often crash the kernel.

        # TODO: also exclude keys when numpy array?
        exclude_keys = {"table_buffer"}
        for key in super()._repr_keys():
            if key in exclude_keys:
                continue

            yield key


class PointLayer(BaseLayer):
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
    get_radius = traitlets.Float(allow_none=True).tag(sync=True)
    get_fill_color = traitlets.List(
        traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
    ).tag(sync=True)
    get_line_color = traitlets.List(
        traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
    ).tag(sync=True)
    get_line_width = traitlets.Float(allow_none=True).tag(sync=True)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> PointLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.point"
        ), "Only Point geometries are currently supported by this layer."

        with BytesIO() as bio:
            feather.write_feather(table, bio, compression="uncompressed")
            return cls(table_buffer=bio.getvalue(), **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> PointLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)


class LineStringLayer(BaseLayer):
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
    get_color = traitlets.List(
        traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
    ).tag(sync=True)
    get_width = traitlets.Float(allow_none=True).tag(sync=True)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> LineStringLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.linestring"
        ), "Only LineString geometries are currently supported by this layer."

        with BytesIO() as bio:
            feather.write_feather(table, bio, compression="uncompressed")
            return cls(table_buffer=bio.getvalue(), **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> LineStringLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)


class PolygonLayer(BaseLayer):
    _layer_type = traitlets.Unicode("solid-polygon").tag(sync=True)

    table_buffer = traitlets.Bytes().tag(sync=True)

    filled = traitlets.Bool(allow_none=True).tag(sync=True)
    extruded = traitlets.Bool(allow_none=True).tag(sync=True)
    wireframe = traitlets.Bool(allow_none=True).tag(sync=True)
    elevation_scale = traitlets.Float(allow_none=True).tag(sync=True)
    get_elevation = traitlets.Float(allow_none=True).tag(sync=True)
    get_fill_color = traitlets.List(
        traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
    ).tag(sync=True)
    get_line_color = traitlets.List(
        traitlets.Int(), None, minlen=3, maxlen=4, allow_none=True
    ).tag(sync=True)

    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> PolygonLayer:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.polygon"
        ), "Only Polygon geometries are currently supported by this layer."

        with BytesIO() as bio:
            feather.write_feather(table, bio, compression="uncompressed")
            return cls(table_buffer=bio.getvalue(), **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> PolygonLayer:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)

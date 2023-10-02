from __future__ import annotations

import psygnal
import pathlib
from io import BytesIO
from anywidget.experimental import widget
import anywidget
import geopandas as gpd
import pyarrow as pa
import pyarrow.feather as feather
from pydantic import BaseModel
import traitlets

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = pathlib.Path(__file__).parent / "static"
_css = bundler_output_dir / "styles.css"


@widget(esm=bundler_output_dir / "polygon.js")
@psygnal.evented
class PolygonModel(BaseModel):
    table_buffer: bytes

    def _get_anywidget_state(self, include):
        state = self.model_dump(exclude={"table_buffer"}, mode="json")
        state["table_buffer"] = self.table_buffer
        return state


    @classmethod
    def from_pyarrow(cls, table: pa.Table, **kwargs) -> PolygonModel:
        assert (
            table.schema.field("geometry").metadata.get(b"ARROW:extension:name")
            == b"geoarrow.polygon"
        ), "Only Polygon geometries are currently supported by this layer."

        with BytesIO() as bio:
            feather.write_feather(table, bio, compression="uncompressed")
            return cls(table_buffer=bio.getvalue(), **kwargs)

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame, **kwargs) -> PolygonModel:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table, **kwargs)

class PointLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "point.js"

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


class LineStringLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "linestring.js"

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


class PolygonLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "polygon.js"

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

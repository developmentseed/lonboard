from __future__ import annotations

import pathlib
from io import BytesIO

import anywidget
import geopandas as gpd
import psygnal
import pyarrow as pa
import pyarrow.feather as feather
import traitlets
from anywidget.experimental import widget
from pydantic import BaseModel

from lonboard.geoarrow.geopandas_interop import geopandas_to_geoarrow

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = pathlib.Path(__file__).parent / "static"
_css = bundler_output_dir / "styles.css"

import ipywidgets

# ipywidgets.link
# ipywidgets.dlink?


import anywidget

class Map(anywidget.AnyWidget):
    _esm = bundler_output_dir / "index.js"

    # TODO: make this an instance of BaseLayer
    value = traitlets.Int(0)
    layers = traitlets.List(
        trait=traitlets.Instance(ipywidgets.DOMWidget)
    ).tag(sync=True, **ipywidgets.widget_serialization)

def _widget_to_json(x, obj):
    print(x)
    print(obj)

class Test(anywidget.AnyWidget):
    value = traitlets.Int(0).tag(sync=True, to_json=_widget_to_json)


# class Map(anywidget.AnyWidget):
#     _esm = """
#     async function unpack_models(model_ids, manager) {
#         return Promise.all(
#             model_ids.map(id => manager.get_model(id.slice("IPY_MODEL_".length)))
#         );
#     }
#     export async function render({ model, el }) {
#        let model_ids = model.get("layers");
#         let children_models = await unpack_models(model_ids, model.widget_manager);
#         for (let model of children_models) {
#             let child_view = await model.widget_manager.create_view(model);
#             el.appendChild(child_view.el);
#         }
#     }
#     """
#     value = traitlets.Int(0)
#     layers = traitlets.List(
#         trait=traitlets.Instance(ipywidgets.DOMWidget)
#     ).tag(sync=True, **ipywidgets.widget_serialization)


class PointLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "point.js"

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


class LineStringLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "linestring.js"

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


class PolygonLayer(anywidget.AnyWidget):
    _esm = bundler_output_dir / "polygon.js"

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

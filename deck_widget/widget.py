from __future__ import annotations

import pathlib
from io import BytesIO

import anywidget
import geopandas as gpd
import pyarrow as pa
import pyarrow.feather as feather
import traitlets

from deck_widget.geoarrow.geopandas_interop import geopandas_to_geoarrow

# bundler yields deck_widget/static/{index.js,styles.css}
bundler_output_dir = pathlib.Path(__file__).parent / "static"
_esm = bundler_output_dir / "index.js"
_css = bundler_output_dir / "styles.css"


class PointLayer(anywidget.AnyWidget):
    _esm = _esm
    _css = _css
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

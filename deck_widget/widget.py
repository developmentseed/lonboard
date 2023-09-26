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

class DeckWidget(anywidget.AnyWidget):
    _esm = bundler_output_dir / "index.js"
    _css = bundler_output_dir / "styles.css"
    buffer = traitlets.Bytes().tag(sync=True)

    @classmethod
    def from_pyarrow(cls, table: pa.Table) -> DeckWidget:
        with BytesIO() as bio:
            feather.write_feather(table, bio, compression="uncompressed")
            return cls(buffer=bio.getvalue())

    @classmethod
    def from_geopandas(cls, gdf: gpd.GeoDataFrame) -> DeckWidget:
        table = geopandas_to_geoarrow(gdf)
        return cls.from_pyarrow(table)


from __future__ import annotations

import pathlib

import anywidget
import ipywidgets
import traitlets

from lonboard.layer import BaseLayer

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = pathlib.Path(__file__).parent / "static"
_css = bundler_output_dir / "styles.css"


class Map(anywidget.AnyWidget):
    _esm = bundler_output_dir / "index.js"

    layers = traitlets.List(trait=traitlets.Instance(BaseLayer)).tag(
        sync=True, **ipywidgets.widget_serialization
    )

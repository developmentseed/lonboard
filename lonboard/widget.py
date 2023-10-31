from __future__ import annotations

from pathlib import Path

import anywidget
import ipywidgets
import traitlets

from lonboard.layer import BaseLayer

# bundler yields lonboard/static/{index.js,styles.css}
bundler_output_dir = Path(__file__).parent / "static"


class Map(anywidget.AnyWidget):
    _esm = bundler_output_dir / "index.js"
    _css = bundler_output_dir / "index.css"

    _initial_view_state = traitlets.Dict().tag(sync=True)

    layers = traitlets.List(trait=traitlets.Instance(BaseLayer)).tag(
        sync=True, **ipywidgets.widget_serialization
    )

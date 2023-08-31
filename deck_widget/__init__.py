import pathlib
import anywidget
import traitlets

# bundler yields deck_widget/static/{index.js,styles.css}
bundler_output_dir = pathlib.Path(__file__).parent / "static"

class DeckWidget(anywidget.AnyWidget):
    _esm = bundler_output_dir / "index.js"
    _css = bundler_output_dir / "styles.css"
    name = traitlets.Unicode().tag(sync=True)
    buffer = traitlets.Bytes().tag(sync=True)

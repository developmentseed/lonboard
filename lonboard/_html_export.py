from __future__ import annotations

from io import StringIO
from typing import IO, TYPE_CHECKING, TextIO, overload

from ipywidgets.embed import dependency_state, embed_minimal_html

if TYPE_CHECKING:
    from pathlib import Path

    from lonboard import Map


# HTML template to override exported map as 100% height
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<style>
    html {{ height: 100%; }}
    body {{ height: 100%; overflow: hidden;}}
    .widget-subarea {{ height: 100%; }}
    .jupyter-widgets-disconnected {{ height: 100%; }}
</style>
<body>
{snippet}
</body>
</html>
"""


@overload
def map_to_html(
    m: Map,
    *,
    filename: None = None,
    title: str | None = None,
) -> str: ...


@overload
def map_to_html(
    m: Map,
    *,
    filename: str | Path | TextIO | IO[str],
    title: str | None = None,
) -> None: ...


def map_to_html(
    m: Map,
    *,
    filename: str | Path | TextIO | IO[str] | None = None,
    title: str | None = None,
) -> str | None:
    def inner(fp: str | Path | TextIO | IO[str]) -> None:
        original_height = m.height
        try:
            with m.hold_trait_notifications():
                m.height = "100%"
                embed_minimal_html(
                    fp,
                    views=[m],
                    title=title or "Lonboard export",
                    template=_HTML_TEMPLATE,
                    drop_defaults=False,
                    # Necessary to pass the state of _this_ specific map. Otherwise, the
                    # state of all known widgets will be included, ballooning the file size.
                    state=dependency_state((m), drop_defaults=False),
                )
        finally:
            # If the map had a height before the HTML was generated, reset it.
            m.height = original_height

    if filename is None:
        with StringIO() as sio:
            inner(sio)
            return sio.getvalue()

    else:
        inner(filename)
        return None

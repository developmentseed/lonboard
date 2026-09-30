"""mkdocs hook that fixes relative image links in rendered notebook pages.

mkdocs rewrites relative links in Markdown pages so they still resolve after
`use_directory_urls` moves each page into its own directory
(`examples/duckdb.ipynb` is served from `examples/duckdb/`). mkdocs-jupyter
replaces the page's render step, so notebook pages never get that treatment:
an image at `../assets/x.png`, which resolves fine in JupyterLab and on GitHub,
would 404 on the site. This hook adds the missing `../` for notebook pages.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

# The `src` of an <img> unless it's a URL, an absolute path, a data URI or an
# anchor. A regex is enough here: the input is nbconvert's output, we only
# insert a prefix into one attribute, and a miss leaves a link that was
# already broken on the site. Parsing and re-serializing the page instead
# would rewrite all of its markup.
_RELATIVE_IMG_SRC = re.compile(
    r"""(<img\b[^>]*?\ssrc=["'])(?![a-zA-Z][a-zA-Z0-9+.-]*:|/|#)""",
    re.IGNORECASE,
)


def on_page_content(
    html: str,
    page: Page,
    config: MkDocsConfig,
    files: Files,  # noqa: ARG001
) -> str:
    """Prefix relative image paths in notebook pages with `../`."""
    if not page.file.src_path.endswith(".ipynb") or not config["use_directory_urls"]:
        return html
    return _RELATIVE_IMG_SRC.sub(r"\1../", html)

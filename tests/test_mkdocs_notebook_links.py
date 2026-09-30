"""Tests for the `scripts/mkdocs_notebook_links.py` mkdocs hook."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

HOOK = Path(__file__).parents[1] / "scripts" / "mkdocs_notebook_links.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("mkdocs_notebook_links", HOOK)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _page(src_path: str):
    return SimpleNamespace(file=SimpleNamespace(src_path=src_path))


def _render(html: str, src_path: str, *, use_directory_urls: bool = True) -> str:
    hook = _load_hook()
    config = {"use_directory_urls": use_directory_urls}
    return hook.on_page_content(html, _page(src_path), config, files=None)


def test_relative_image_in_notebook_page_goes_up_one_more_level():
    html = '<img src="../assets/duckdb.png" alt="">'
    assert _render(html, "examples/duckdb.ipynb") == (
        '<img src="../../assets/duckdb.png" alt="">'
    )


def test_absolute_and_data_urls_are_untouched():
    html = (
        '<img src="https://example.com/a.png">'
        '<img src="/a.png">'
        '<img src="data:image/png;base64,AAAA">'
    )
    assert _render(html, "examples/duckdb.ipynb") == html


def test_markdown_pages_are_untouched():
    html = '<img src="../assets/duckdb.png">'
    assert _render(html, "examples/index.md") == html


def test_flat_urls_are_untouched():
    html = '<img src="../assets/duckdb.png">'
    assert _render(html, "examples/duckdb.ipynb", use_directory_urls=False) == html

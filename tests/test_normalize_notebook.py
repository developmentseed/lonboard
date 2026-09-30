"""Tests for the `scripts/normalize_notebook.py` pre-commit hook."""

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "normalize_notebook.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("normalize_notebook", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_notebook(path: Path, metadata: dict) -> dict:
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "source": "1 + 1",
                "outputs": [{"output_type": "stream", "name": "stdout", "text": "2"}],
            },
        ],
        "metadata": metadata,
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    return nb


def test_strips_saved_widget_state(tmp_path: Path):
    script = _load_script()
    nb_path = tmp_path / "nb.ipynb"
    _write_notebook(
        nb_path,
        {
            "kernelspec": script.KERNELSPEC,
            "widgets": {"application/vnd.jupyter.widget-state+json": {"state": {}}},
        },
    )

    assert script.normalize(nb_path) is True
    assert "widgets" not in json.loads(nb_path.read_text())["metadata"]


def test_keeps_cell_outputs(tmp_path: Path):
    script = _load_script()
    nb_path = tmp_path / "nb.ipynb"
    original = _write_notebook(nb_path, {"widgets": {}})

    script.normalize(nb_path)

    assert json.loads(nb_path.read_text())["cells"] == original["cells"]


def test_resets_machine_specific_kernelspec(tmp_path: Path):
    script = _load_script()
    nb_path = tmp_path / "nb.ipynb"
    _write_notebook(
        nb_path,
        {"kernelspec": {"name": "lonboard-venv", "language": "python"}},
    )

    assert script.normalize(nb_path) is True
    assert json.loads(nb_path.read_text())["metadata"]["kernelspec"] == (
        script.KERNELSPEC
    )


def test_clean_notebook_is_left_untouched(tmp_path: Path):
    script = _load_script()
    nb_path = tmp_path / "nb.ipynb"
    _write_notebook(nb_path, {"kernelspec": script.KERNELSPEC})
    before = nb_path.read_bytes()

    assert script.normalize(nb_path) is False
    assert nb_path.read_bytes() == before

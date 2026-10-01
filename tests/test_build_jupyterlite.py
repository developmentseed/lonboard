"""Tests for `scripts/build_jupyterlite.py`."""

import importlib.util
import json
import stat
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "build_jupyterlite.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("build_jupyterlite", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load_script()

PYTHON3_KERNELSPEC = {
    "display_name": "Python 3 (ipykernel)",
    "language": "python",
    "name": "python3",
}
NOTEBOOKS = [Path("more/nested.ipynb"), Path("top.ipynb")]


def _write_notebook(
    path: Path,
    *,
    metadata: dict | None = None,
    outputs: list | None = None,
    execution_count: int | None = None,
) -> Path:
    if metadata is None:
        metadata = {
            "kernelspec": script.PYODIDE_KERNELSPEC,
            "language_info": {"name": "python"},
        }
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": execution_count,
                "id": "a1",
                "metadata": {},
                "outputs": outputs or [],
                "source": "import lonboard",
            },
        ],
        "metadata": metadata,
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    return path


def test_clean_pyodide_notebook_has_no_problems(tmp_path: Path):
    nb = _write_notebook(tmp_path / "nb.ipynb")
    assert script.notebook_problems(nb) == []


def test_python3_kernelspec_is_a_problem(tmp_path: Path):
    nb = _write_notebook(
        tmp_path / "nb.ipynb",
        metadata={
            "kernelspec": PYTHON3_KERNELSPEC,
            "language_info": {"name": "python"},
        },
    )
    problems = script.notebook_problems(nb)
    assert len(problems) == 1
    assert "kernelspec" in problems[0]


def test_missing_language_info_is_a_problem(tmp_path: Path):
    nb = _write_notebook(
        tmp_path / "nb.ipynb",
        metadata={"kernelspec": script.PYODIDE_KERNELSPEC},
    )
    problems = script.notebook_problems(nb)
    assert len(problems) == 1
    assert "language_info" in problems[0]


def test_outputs_are_a_problem(tmp_path: Path):
    nb = _write_notebook(
        tmp_path / "nb.ipynb",
        outputs=[{"output_type": "stream", "name": "stdout", "text": "hi"}],
        execution_count=1,
    )
    problems = script.notebook_problems(nb)
    assert len(problems) == 1
    assert "outputs" in problems[0]


def test_saved_widget_state_is_a_problem(tmp_path: Path):
    nb = _write_notebook(
        tmp_path / "nb.ipynb",
        metadata={
            "kernelspec": script.PYODIDE_KERNELSPEC,
            "language_info": {"name": "python"},
            "widgets": {"application/vnd.jupyter.widget-state+json": {"state": {}}},
        },
    )
    problems = script.notebook_problems(nb)
    assert len(problems) == 1
    assert "widget state" in problems[0]


def test_desktop_saved_notebook_reports_every_problem(tmp_path: Path):
    nb = _write_notebook(
        tmp_path / "nb.ipynb",
        metadata={
            "kernelspec": PYTHON3_KERNELSPEC,
            "widgets": {"application/vnd.jupyter.widget-state+json": {"state": {}}},
        },
        outputs=[{"output_type": "stream", "name": "stdout", "text": "hi"}],
        execution_count=3,
    )
    problems = script.notebook_problems(nb)
    assert len(problems) == 4
    assert all(str(nb) in problem for problem in problems)


def _release(*filenames: str) -> dict:
    return {
        "info": {"version": "0.11.0"},
        "urls": [
            {"filename": name, "url": f"https://files.pythonhosted.org/{name}"}
            for name in filenames
        ],
    }


def test_wheel_url_picks_the_pure_python_wheel():
    release = _release(
        "anywidget-0.11.0.tar.gz",
        "anywidget-0.11.0-py3-none-any.whl",
    )
    assert (
        script.wheel_url(release, "anywidget")
        == "https://files.pythonhosted.org/anywidget-0.11.0-py3-none-any.whl"
    )


@pytest.mark.parametrize(
    "filenames",
    [
        ("anywidget-0.11.0.tar.gz",),
        ("anywidget-0.11.0-py3-none-any.whl", "anywidget-0.11.0-py3-none-any.whl"),
    ],
)
def test_wheel_url_rejects_a_release_without_exactly_one_pure_wheel(filenames):
    with pytest.raises(ValueError, match=r"anywidget 0\.11\.0"):
        script.wheel_url(_release(*filenames), "anywidget")


def test_read_only_copy_makes_every_notebook_read_only(tmp_path: Path):
    content = tmp_path / "content"
    _write_notebook(content / "top.ipynb")
    _write_notebook(content / "more" / "nested.ipynb")
    (content / "data.csv").write_text("a,b\n", encoding="utf-8")
    dest = tmp_path / "copy"

    notebooks = script.read_only_copy(content, dest)

    assert notebooks == NOTEBOOKS
    for notebook in notebooks:
        assert not (dest / notebook).stat().st_mode & 0o222
        assert (content / notebook).stat().st_mode & stat.S_IWUSR
    assert (dest / "data.csv").read_text(encoding="utf-8") == "a,b\n"


def test_read_only_copy_skips_checkpoints(tmp_path: Path):
    content = tmp_path / "content"
    _write_notebook(content / "top.ipynb")
    _write_notebook(content / ".ipynb_checkpoints" / "top-checkpoint.ipynb")

    notebooks = script.read_only_copy(content, tmp_path / "copy")

    assert notebooks == [Path("top.ipynb")]
    assert not (tmp_path / "copy" / ".ipynb_checkpoints").exists()


def test_remove_previous_build_deletes_an_earlier_site(tmp_path: Path):
    site = tmp_path / "site"
    (site / "files").mkdir(parents=True)
    (site / "jupyter-lite.json").write_text("{}", encoding="utf-8")
    old = site / "files" / "nb.ipynb"
    old.write_text("{}", encoding="utf-8")
    old.chmod(0o444)

    script.remove_previous_build(site)

    assert not site.exists()


def test_remove_previous_build_leaves_a_missing_or_empty_dir(tmp_path: Path):
    script.remove_previous_build(tmp_path / "missing")
    (tmp_path / "empty").mkdir()
    script.remove_previous_build(tmp_path / "empty")
    assert (tmp_path / "empty").is_dir()


@pytest.mark.parametrize("name", ["jupyter_lite_config.json", "README.md"])
def test_remove_previous_build_refuses_other_dirs(tmp_path: Path, name: str):
    (tmp_path / name).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Refusing"):
        script.remove_previous_build(tmp_path)
    assert (tmp_path / name).exists()


def _fake_site(
    tmp_path: Path,
    *,
    writable: bool = False,
    releases: dict[str, list[str]] | None = None,
) -> Path:
    """Write the parts of a built site that `output_problems` reads."""
    if releases is None:
        releases = {"anywidget": ["0.11.0"]}
    site = tmp_path / "site"
    (site / "files" / "more").mkdir(parents=True)
    (site / "files" / "top.ipynb").write_text("{}", encoding="utf-8")
    (site / "files" / "more" / "nested.ipynb").write_text("{}", encoding="utf-8")
    contents = site / "api" / "contents"
    (contents / "more").mkdir(parents=True)
    (contents / "all.json").write_text(
        json.dumps(
            {
                "content": [
                    {"name": "more", "type": "directory", "writable": True},
                    {"name": "top.ipynb", "type": "notebook", "writable": writable},
                ],
            },
        ),
        encoding="utf-8",
    )
    (contents / "more" / "all.json").write_text(
        json.dumps(
            {
                "content": [
                    {"name": "nested.ipynb", "type": "notebook", "writable": writable},
                ],
            },
        ),
        encoding="utf-8",
    )
    (site / "pypi").mkdir()
    index = {
        name: {"releases": {v: [] for v in versions}}
        for name, versions in releases.items()
    }
    (site / "pypi" / "all.json").write_text(json.dumps(index), encoding="utf-8")
    return site


def test_output_problems_accepts_a_good_site(tmp_path: Path):
    assert script.output_problems(_fake_site(tmp_path), NOTEBOOKS, "0.11.0") == []


def test_writable_notebooks_are_a_problem(tmp_path: Path):
    site = _fake_site(tmp_path, writable=True)
    problems = script.output_problems(site, NOTEBOOKS, "0.11.0")
    assert len(problems) == 2
    assert all("read-only" in problem for problem in problems)


def test_missing_notebook_is_a_problem(tmp_path: Path):
    site = _fake_site(tmp_path)
    (site / "files" / "top.ipynb").unlink()
    problems = script.output_problems(site, NOTEBOOKS, "0.11.0")
    assert len(problems) == 1
    assert "top.ipynb" in problems[0]
    assert "missing" in problems[0]


@pytest.mark.parametrize(
    "releases",
    [
        # A wheel left over from an earlier build
        {"anywidget": ["0.10.0", "0.11.0"]},
        # A bundled lonboard would freeze the site on that version
        {"anywidget": ["0.11.0"], "lonboard": ["0.17.0"]},
        # A different anywidget than the one whose frontend the site bundles
        {"anywidget": ["0.10.0"]},
        {},
    ],
)
def test_bundled_index_must_hold_only_the_matching_anywidget(
    tmp_path: Path,
    releases: dict[str, list[str]],
):
    site = _fake_site(tmp_path, releases=releases)
    problems = script.output_problems(site, NOTEBOOKS, "0.11.0")
    assert len(problems) == 1
    assert "pypi/all.json" in problems[0]


def test_missing_bundled_index_is_a_problem(tmp_path: Path):
    site = _fake_site(tmp_path)
    (site / "pypi" / "all.json").unlink()
    problems = script.output_problems(site, NOTEBOOKS, "0.11.0")
    assert len(problems) == 1
    assert "pypi/all.json" in problems[0]

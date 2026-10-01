"""Build the JupyterLite site that the docs link to.

Run from the repository root, with the `jupyterlite` dependency group only:

    uv run --locked --only-group jupyterlite python scripts/build_jupyterlite.py

The site goes to `jupyterlite/_output` unless `--output-dir` says otherwise.
`.github/workflows/deploy-jupyterlite.yml` publishes it to
<https://developmentseed.org/lonboard/jupyterlite/>.

Two things differ from a plain `jupyter lite build`:

- The notebooks are served read-only. JupyterLite otherwise saves a visitor's
  copy in their browser once they run it, and that copy hides every later
  deploy from them.
- The site bundles the anywidget wheel that matches the anywidget frontend it
  bundles, and `%pip install` then takes anywidget from the site instead of
  PyPI. anywidget's Python side only works with a frontend of the same minor
  version.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LITE_DIR = ROOT / "jupyterlite"
CONTENT_DIR = LITE_DIR / "content"
DEFAULT_OUTPUT_DIR = LITE_DIR / "_output"
# JupyterLite's build cache, written to the directory the build runs in. A
# stale cache can skip copying the notebooks, which the site then lists as
# writable.
DOIT_DB = LITE_DIR / ".jupyterlite.doit.db"

BUNDLED_PACKAGE = "anywidget"
PYODIDE_KERNELSPEC = {
    "display_name": "Python (Pyodide)",
    "language": "python",
    "name": "python",
}


def notebook_problems(path: Path) -> list[str]:
    """Return why a notebook can't be published as it is, one message per problem.

    Without the Pyodide kernelspec (or at least `language_info.name`),
    JupyterLite asks every visitor to pick a kernel. Saved outputs and widget
    state would show stale results before the visitor runs anything.
    """
    nb = json.loads(path.read_text(encoding="utf-8"))
    metadata = nb.get("metadata", {})
    problems = []
    if metadata.get("kernelspec") != PYODIDE_KERNELSPEC:
        problems.append(f"{path}: set the kernelspec to {PYODIDE_KERNELSPEC}")
    if metadata.get("language_info", {}).get("name") != "python":
        problems.append(f'{path}: set language_info.name to "python"')
    if any(cell.get("outputs") or cell.get("execution_count") for cell in nb["cells"]):
        problems.append(f"{path}: clear the outputs")
    if "widgets" in metadata:
        problems.append(f"{path}: remove the saved widget state")
    return problems


def wheel_url(release: dict, name: str) -> str:
    """Return the URL of the one `py3-none-any` wheel in a release from PyPI's JSON API."""
    urls = [
        file["url"]
        for file in release["urls"]
        if file["filename"].endswith("-py3-none-any.whl")
    ]
    if len(urls) != 1:
        msg = (
            f"Expected one py3-none-any wheel for {name} "
            f"{release['info']['version']} on PyPI, found {len(urls)}"
        )
        raise ValueError(msg)
    return urls[0]


def read_only_copy(content_dir: Path, dest: Path) -> list[Path]:
    """Copy `content_dir` to `dest` and make the copied notebooks read-only.

    jupyter-server lists a read-only file with `"writable": false`, and
    JupyterLite never saves such a notebook into the visitor's browser. Returns
    the notebooks' paths relative to `dest`.
    """
    shutil.copytree(
        content_dir,
        dest,
        ignore=shutil.ignore_patterns(".ipynb_checkpoints"),
    )
    notebooks = sorted(path.relative_to(dest) for path in dest.rglob("*.ipynb"))
    for notebook in notebooks:
        (dest / notebook).chmod(0o444)
    return notebooks


def remove_previous_build(output_dir: Path) -> None:
    """Delete an earlier build in `output_dir`, and refuse to delete anything else.

    Building into a fresh directory matters: JupyterLite's build cache can keep
    a notebook listed as writable, and the site indexes every wheel left in
    `pypi/`.
    """
    if not output_dir.exists() or not any(output_dir.iterdir()):
        return
    if not (output_dir / "jupyter-lite.json").is_file():
        msg = (
            f"Refusing to delete {output_dir}: "
            "it isn't empty and doesn't hold a JupyterLite build"
        )
        raise ValueError(msg)
    shutil.rmtree(output_dir)


def output_problems(
    output_dir: Path,
    notebooks: list[Path],
    anywidget_version: str,
) -> list[str]:
    """Return what's wrong with a built site, one message per problem."""
    problems = []
    for notebook in notebooks:
        if not (output_dir / "files" / notebook).is_file():
            problems.append(f"{notebook} is missing from {output_dir / 'files'}")
            continue
        listing = output_dir / "api" / "contents" / notebook.parent / "all.json"
        entries = json.loads(listing.read_text(encoding="utf-8"))["content"]
        if not any(
            entry["name"] == notebook.name and entry.get("writable") is False
            for entry in entries
        ):
            problems.append(f"{notebook} isn't read-only in {listing}")

    index_path = output_dir / "pypi" / "all.json"
    index = (
        json.loads(index_path.read_text(encoding="utf-8"))
        if index_path.is_file()
        else {}
    )
    bundled = {name: sorted(entry["releases"]) for name, entry in index.items()}
    expected = {BUNDLED_PACKAGE: [anywidget_version]}
    if bundled != expected:
        problems.append(f"pypi/all.json should bundle {expected}, not {bundled}")
    return problems


def fetch_release(name: str, release_version: str) -> dict:
    """Return PyPI's JSON description of one release of a package."""
    url = f"https://pypi.org/pypi/{name}/{release_version}/json"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main() -> None:
    """Build the site, and fail unless it can be published."""
    parser = argparse.ArgumentParser(description="Build the JupyterLite site.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="where to write the site (default: jupyterlite/_output)",
    )
    # Resolve against the directory the script runs from: the build itself
    # runs in jupyterlite/
    output_dir = parser.parse_args().output_dir.resolve()

    anywidget_version = version(BUNDLED_PACKAGE)
    release = fetch_release(BUNDLED_PACKAGE, anywidget_version)
    wheel = wheel_url(release, BUNDLED_PACKAGE)
    print(f"Bundling {BUNDLED_PACKAGE} {anywidget_version}: {wheel}")

    with tempfile.TemporaryDirectory() as tmp:
        content = Path(tmp) / "content"
        notebooks = read_only_copy(CONTENT_DIR, content)
        problems = [
            problem
            for notebook in notebooks
            for problem in notebook_problems(CONTENT_DIR / notebook)
        ]
        if problems:
            raise SystemExit("\n".join(problems))
        try:
            remove_previous_build(output_dir)
        except ValueError as e:
            raise SystemExit(str(e)) from e
        DOIT_DB.unlink(missing_ok=True)
        subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "jupyterlite_core",
                "build",
                "--contents",
                str(content),
                "--output-dir",
                str(output_dir),
                "--piplite-wheels",
                wheel,
            ],
            cwd=LITE_DIR,
            check=True,
        )

    problems = output_problems(output_dir, notebooks, anywidget_version)
    if problems:
        raise SystemExit("\n".join(problems))
    print(f"Built the JupyterLite site in {output_dir}")


if __name__ == "__main__":
    main()

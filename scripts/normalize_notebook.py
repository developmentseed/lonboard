"""Normalize the metadata of example notebooks.

`kernelspec`: Jupyter stores the name of whatever kernel last ran a notebook in
its metadata. When that is a machine-specific kernel (e.g. one registered from
this repo's `.venv`), JupyterLab will resolve it ahead of the environment it was
launched in. For notebooks with PEP 723 inline metadata that means `juv run`
builds the correct environment but the notebook executes somewhere else
entirely, and dependencies appear to be missing. Rewriting the kernelspec to
the generic `python3` makes the notebook resolve to whichever environment
opened it.

`widgets`: saving a notebook with "Save Widget State" embeds the state of every
widget, including a copy of lonboard's JS bundle for each map. That adds
megabytes to the notebook and to every rendered docs page, without making the
maps render there, since the layer data is not part of the saved state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KERNELSPEC = {
    "display_name": "Python 3 (ipykernel)",
    "language": "python",
    "name": "python3",
}


def normalize(path: Path) -> bool:
    """Rewrite `path`'s metadata in place, returning whether it changed."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    metadata = nb.setdefault("metadata", {})
    if metadata.get("kernelspec") == KERNELSPEC and "widgets" not in metadata:
        return False

    metadata["kernelspec"] = KERNELSPEC
    metadata.pop("widgets", None)
    # Matches how nbformat itself writes notebooks, so the diff stays minimal.
    path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def main(argv: list[str]) -> int:
    """Normalize each notebook passed on the command line."""
    changed = [Path(arg) for arg in argv if normalize(Path(arg))]
    for path in changed:
        print(f"normalized notebook metadata: {path}")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

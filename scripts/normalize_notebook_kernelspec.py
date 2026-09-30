"""Normalize the `kernelspec` metadata of example notebooks.

Jupyter stores the name of whatever kernel last ran a notebook in its metadata.
When that is a machine-specific kernel (e.g. one registered from this repo's
`.venv`), JupyterLab will resolve it ahead of the environment it was launched
in. For notebooks with PEP 723 inline metadata that means `juv run` builds the
correct environment but the notebook executes somewhere else entirely, and
dependencies appear to be missing.

Rewriting the kernelspec to the generic `python3` makes the notebook resolve
to whichever environment opened it.
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
    """Rewrite `path`'s kernelspec in place, returning whether it changed."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    if nb.get("metadata", {}).get("kernelspec") == KERNELSPEC:
        return False

    nb.setdefault("metadata", {})["kernelspec"] = KERNELSPEC
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
        print(f"normalized kernelspec: {path}")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

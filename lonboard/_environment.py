from __future__ import annotations

import os
from pathlib import Path

from lonboard._constants import Environment

try:
    import IPython
except ImportError:
    IPython = None


def detect_environment() -> Environment:  # noqa: PLR0911
    """Try to detect user's environment.

    This is ported from Plotly here:
    https://github.com/plotly/plotly.py/blob/38ded4acc91bd6c33fbe2c8090d629ba2215dce1/packages/python/plotly/plotly/io/_renderers.py#L446C1-L538C37
    under the MIT license.
    """
    if IPython and IPython.get_ipython():
        try:
            import google.colab  # noqa: F401

            return Environment.Colab  # noqa: TRY300
        except ImportError:
            pass

    if Path("/kaggle/input").exists():
        return Environment.Kaggle

    if "AZURE_NOTEBOOKS_HOST" in os.environ:
        return Environment.Azure

    if "VSCODE_PID" in os.environ:
        return Environment.Vscode

    if "NTERACT_EXE" in os.environ:
        return Environment.Nteract

    if "COCALC_PROJECT_ID" in os.environ:
        return Environment.Cocalc

    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        return Environment.Databricks

    if IPython.get_ipython().__class__.__name__ == "TerminalInteractiveShell":
        return Environment.IPythonTerminal

    return Environment.Unknown


ENVIRONMENT = detect_environment()


DEFAULT_HEIGHT = "500px"

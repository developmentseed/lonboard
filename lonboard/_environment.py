import os

from lonboard._constants import Environment

try:
    import IPython
except ImportError:
    IPython = None


def detect_environment() -> Environment:
    """Try to detect user's environment

    This is ported from Plotly here:
    https://github.com/plotly/plotly.py/blob/38ded4acc91bd6c33fbe2c8090d629ba2215dce1/packages/python/plotly/plotly/io/_renderers.py#L446C1-L538C37
    under the MIT license.
    """
    if IPython and IPython.get_ipython():
        try:
            import google.colab  # noqa: F401

            return Environment.Colab
        except ImportError:
            pass

    if os.path.exists("/kaggle/input"):
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


def default_height():
    if ENVIRONMENT in [Environment.Vscode, Environment.Colab]:
        return 500

    return None


DEFAULT_HEIGHT = default_height()

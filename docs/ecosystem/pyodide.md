# Pyodide

Lonboard works in [Pyodide](https://pyodide.org/), which runs Python _inside your web browser_ with WebAssembly. That includes [JupyterLite](https://jupyterlite.readthedocs.io/), a Jupyter environment that needs no server and no install.

[Try it in your browser](https://developmentseed.org/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb){ .md-button .md-button--primary }

[![Lonboard mapping the boroughs of New York City in JupyterLite](../assets/lonboard-jupyterlite.jpg)](https://developmentseed.org/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb)

The demo notebook installs Lonboard and maps the boroughs of New York City:

```py
%pip install lonboard geopandas requests pyarrow

from io import BytesIO
from zipfile import ZipFile

import geopandas as gpd
import requests

import lonboard

url = "https://cdn.jsdelivr.net/gh/geopandas/geodatasets@2026.5.1/data_backup/nybb_16a.zip"
r = requests.get(url)
with ZipFile(BytesIO(r.content)) as z:
    z.extractall("/tmp/nybb")

gdf = gpd.read_file("/tmp/nybb/nybb_16a/nybb.shp").to_crs("EPSG:4326")
lonboard.viz(gdf)
```

## What to expect

- The first run downloads Python and the packages, about 65 MB, so it takes tens of seconds. Your browser caches them for later visits.
- The notebook is read-only. You can edit and run any cell, but your changes are lost when you reload, and your browser warns you before you leave. To keep them, use **File > Save As**, then choose **Discard** when JupyterLite asks about `getting-started.ipynb`.

## Installing packages

Install packages with `%pip install` in a notebook cell:

- Pure-Python packages work as they are. Packages with compiled code need wheels built for Pyodide, either [included in Pyodide](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) or published on PyPI.
- Lonboard needs `pyarrow` to read a GeoDataFrame, so install it alongside.
- `%pip install --pre lonboard` installs the latest pre-release, if you want to try a beta.
- Don't use `-U` or `--upgrade`: JupyterLite doesn't support it, and skips the whole line without installing anything.

## Memory limits

Pyodide has stricter memory limits than normal Python environments. Take care to delete Python objects you're no longer using with `del`.

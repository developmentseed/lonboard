# Developer Documentation

## Clone repository

The repository is rather large because the website is published and saved for _every_ Python tag and release. So the example notebooks are duplicated for every version.

It's suggested to perform a shallow clone of the repository for development without the `gh-pages` branch:

```bash
git clone --depth 1 https://github.com/developmentseed/lonboard.git
```

## Python

Install [uv](https://docs.astral.sh/uv/).

To register the current uv-managed Python environment with JupyterLab, run

```
uv run python -m ipykernel install --user --name "lonboard"
```

JupyterLab is an included dev dependency, so to start JupyterLab you can run

```
ANYWIDGET_HMR=1 uv run --group watchfiles jupyter lab
```

Note that `ANYWIDGET_HMR=1` is necessary to turn on "hot-reloading", so that any
updates you make in JavaScript code are automatically updated in your notebook.

Then you should see a tile on the home screen that lets you open a Jupyter Notebook in the `lonboard` environment. You should also be able to open up an example notebook from the `examples/` folder.

## JavaScript

Requirements:

- [Node](http://nodejs.org/) (see version in [.nvmrc](./.nvmrc) or `"volta"` section of `package.json`) or use [nvm](https://github.com/creationix/nvm) or [Volta](https://volta.sh).

Install module dependencies:

```sh
pnpm install
```

We use ESBuild to bundle into an ES Module, which the Jupyter Widget will then load at runtime. The configuration for ESBuild can be found in `build.mjs`. To start watching for changes in the `/src` folder and automatically generate a new build, use:

```sh
pnpm build:watch
```

Unit tests for the TypeScript code live in `src/tests/` and use [Vitest](https://vitest.dev/). To run them:

```sh
pnpm test
```

### Environment Variables

To use custom environment variables, you can create a file `.env`:

```bash
VARIABLE="setting"
```

This file contains the list of environment variables for the JavaScript component, and the build task will use them when available.

**Note: `.env` is in `.gitignore` and should never be committed.**

### Architectural notes

All models on the TypeScript side are combined into a single entry point, which is compiled by ESBuild and loaded by the Python `Map` class. (Refer to the `_esm` key on the `Map` class, which tells Jupyter/ipywidgets where to load the JavaScript bundle.)

Anywidget and its dependency ipywidgets handles the serialization from Python into JS, automatically keeping each side in sync.

### Developing against local packages

E.g. to test against a local copy of `deck.gl-raster`:

```bash
pnpm link ../deck.gl-raster/packages/*
```

You'll also want to ensure that deck.gl versions in both projects are pinned
exactly the same.

## Linting and formatting

We use [pre-commit](https://pre-commit.com/) to run a few fast checks before each commit. The hooks are defined in [`.pre-commit-config.yaml`](./.pre-commit-config.yaml).

Install the hooks once after cloning the repository:

```
uv run pre-commit install
```

To run the hooks on every file without making a commit:

```
uv run pre-commit run --all-files
```

CI runs the same command.

pre-commit runs each hook in an environment of its own, without the dependencies of the project. So the hooks only do checks that need nothing but the source files, and they don't run the tests.

### Javascript

The hooks don't check the JavaScript code. [Biome](https://biomejs.dev/) lints and formats it, and CI fails if `pnpm check` reports a problem. To apply the fixes that Biome can make by itself:

```sh
pnpm check:fix
```

## Publishing

Bump the version with `uv version <new version>`, which updates `pyproject.toml` and `uv.lock` together. If you edit `pyproject.toml` by hand, run `uv lock` afterwards. Otherwise the JupyterLite build check, which runs uv with `--locked`, fails on the stale lock.

Push a new tag to the main branch of the format `v*`. A new version will be published to PyPI automatically.

## Documentation website

The documentation website is generated with `mkdocs` and [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material). You can serve the docs website locally with

```
uv run --group docs mkdocs serve
```

Publishing documentation happens automatically via CI when a new tag is published of the format `v*`. Docs are published per minor version (`v0.17`, not `v0.17.2`), so a patch release replaces the docs of its minor rather than adding another copy to the `gh-pages` branch. It can also be triggered manually through the Github Actions dashboard on [this page](https://github.com/developmentseed/lonboard/actions/workflows/deploy-mkdocs.yml). Note that publishing docs manually is **not advised if there have been new code additions since the last release** as the new functionality will be associated in the documentation with the tag of the _previous_ release. In this case, prefer publishing a new patch or minor release, which will publish both a new Python package and the new documentation for it.

Note that the `jupyter-mkdocs` plugin is only turned on when the `CI` env variable is set. If you're inspecting the docs with a Jupyter notebook, start the local dev server with:

```
CI=true uv run --group docs mkdocs serve
```

## JupyterLite site

The docs link to a [JupyterLite](https://jupyterlite.readthedocs.io/) site, <https://developmentseed.org/lonboard/jupyterlite/>, that runs the notebooks in `jupyterlite/content/` in the browser with Pyodide. After CI publishes the docs of a stable release, [`deploy-jupyterlite.yml`](.github/workflows/deploy-jupyterlite.yml) builds the site and publishes it, unversioned, to the `jupyterlite/` folder of the `gh-pages` branch. You can also run that workflow by hand from `main`; with `dry_run` it does everything except the push. Don't publish by hand while the newest release isn't on PyPI, since the notebook installs the latest lonboard from PyPI.

To build the site and preview it locally:

```bash
UV_PROJECT_ENVIRONMENT=.venv-jupyterlite uv run --locked --only-group jupyterlite python scripts/build_jupyterlite.py --output-dir /tmp/lite/lonboard/jupyterlite
python -m http.server --directory /tmp/lite 8000
```

Then open <http://127.0.0.1:8000/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb>. The separate environment matters: the site bundles every JupyterLab extension installed where it's built, and the dev environment has others. The build always warns about translations and `libarchive-c`; both warnings are harmless. To try unreleased changes, run `pnpm build` and `uv build --wheel --out-dir /tmp/lite`, then change the notebook's install line to `%pip install http://127.0.0.1:8000/<wheel file> geopandas requests pyarrow`.

The build script makes these changes:

- It serves the notebooks read-only, so visitors always see the deployed version.
- It bundles the anywidget wheel that matches the site's anywidget frontend, because the two must have the same minor version.
- It fails if a notebook in `jupyterlite/content/` has outputs or lacks the Pyodide kernelspec (`"name": "python"`). The `normalize-notebook` pre-commit hook skips that folder.

The site installs lonboard from PyPI into Pyodide, so:

- lonboard's lower bounds must stay at or below the versions in Pyodide, for example traitlets 5.14.3, numpy 2.4.6 and pyproj 3.7.2;
- a new required dependency must be pure Python, part of Pyodide, or published with `pyemscripten` wheels;
- `jupyterlite-pyodide-kernel` sets the Pyodide version, and a new minor version can move to a new Pyodide ABI. Dependabot skips those updates. Upgrade it by hand once arro3 and geoarrow-rust-core have published wheels for that ABI, and run the notebook in a browser before merging.

## Developing Jupyter Notebook examples

We use `juv` to store dependencies for each notebook as metadata of the notebook itself.

To run an example notebook with a local version of lonboard, first ensure that you have built the JavaScript bundle:

```bash
pnpm build:watch
```

then use:

```bash
ANYWIDGET_HMR=1 uvx juv run --with="../" examples/air-traffic-control.ipynb
```

Note that the path in `--with` is relative to the notebook itself.

### Screenshots in notebooks

Don't paste screenshots into Markdown cells. Jupyter stores them inside the notebook as base64, and every docs release then publishes a fresh copy of each example page, which is [what made the `gh-pages` branch so large](https://github.com/developmentseed/lonboard/issues/1160). Save the image to `assets/` instead and link to it relative to the notebook, e.g. `![](../assets/duckdb-heatmap.jpg)`. The mkdocs hook in `scripts/mkdocs_notebook_links.py` adjusts such links for the site's directory URLs.

Widget state saved in a notebook ("Save Widget State" in JupyterLab) is stripped by the `scripts/normalize_notebook.py` pre-commit hook, since it only holds a copy of the JS bundle and can't render the maps on the docs site anyway.

## Profiling

### Python

I've come to really like [pyinstrument](https://pyinstrument.readthedocs.io/). pyinstrument is already included in the `dev` dependencies, or you can install it with pip. Then, inside a Jupyter notebook, load it with

```py
%load_ext pyinstrument
```

Then you can profile any cell with

```py
%%pyinstrument
# code to profile
m = Map(...)
```

It will print out a nice report right in the notebook.

### Widget display in Python

Sometimes the map _display_ is slow on the Python side. I.e. sometimes the map object generation `m = Map(...)` is fast, but then rendering with `m` in its own cell is slow before reaching JavaScript.

In this case, you can still use `pyinstrument` but you need to opt-in to the _explicit_ display:

```py
from IPython.display import display

%%pyinstrument
display(m)
```

Otherwise, pyinstrument won't be able to hook into the display process.

### JavaScript rendering

Chrome's native performance profiler is the best tool I've used for this so far.

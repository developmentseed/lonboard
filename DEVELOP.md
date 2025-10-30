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
npm install
```

We use ESBuild to bundle into an ES Module, which the Jupyter Widget will then load at runtime. The configuration for ESBuild can be found in `build.mjs`. To start watching for changes in the `/src` folder and automatically generate a new build, use:

```sh
npm run build:watch
```

### Environment Variables

To use custom environment variables, copy the example environment file:

```sh
cp .env.example .env
```

This file contains the list of environment variables for the JavaScript component, and the build task will use them when available.

**Note: `.env` is in `.gitignore` and should never be committed.**

### Architectural notes

All models on the TypeScript side are combined into a single entry point, which is compiled by ESBuild and loaded by the Python `Map` class. (Refer to the `_esm` key on the `Map` class, which tells Jupyter/ipywidgets where to load the JavaScript bundle.)

Anywidget and its dependency ipywidgets handles the serialization from Python into JS, automatically keeping each side in sync.

State management is implemented using [XState](https://stately.ai/docs/xstate). The app is instrumented with [Stately Inspector](https://stately.ai/docs/inspector), and the use of the [VS Code extension](https://stately.ai/docs/xstate-vscode-extension) is highly recommended.

## Publishing

Push a new tag to the main branch of the format `v*`. A new version will be published to PyPI automatically.

## Documentation website

The documentation website is generated with `mkdocs` and [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material). You can serve the docs website locally with

```
uv run --group docs mkdocs serve
```

Publishing documentation happens automatically via CI when a new tag is published of the format `v*`. It can also be triggered manually through the Github Actions dashboard on [this page](https://github.com/developmentseed/lonboard/actions/workflows/deploy-mkdocs.yml). Note that publishing docs manually is **not advised if there have been new code additions since the last release** as the new functionality will be associated in the documentation with the tag of the _previous_ release. In this case, prefer publishing a new patch or minor release, which will publish both a new Python package and the new documentation for it.

Note that the `jupyter-mkdocs` plugin is only turned on when the `CI` env variable is set. If you're inspecting the docs with a Jupyter notebook, start the local dev server with:

```
CI=true uv run --group docs mkdocs serve
```

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

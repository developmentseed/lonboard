# Developer Documentation

## Python

To install Python, I recommend [pyenv](https://github.com/pyenv/pyenv). After installing pyenv, install a Python version with e.g.:

```
pyenv install 3.11.4
```

then set that as your global Python version with

```
pyenv global 3.11.4
```

This project uses [Poetry](https://python-poetry.org/) to manage Python dependencies.

After installing Poetry, run

```
poetry install
```

to install all dependencies.

To register the current Poetry-managed Python environment with JupyterLab, run

```
poetry run python -m ipykernel install --user --name "lonboard"
```

JupyterLab is an included dev dependency, so to start JupyterLab you can run

```
poetry run jupyter lab
```

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

All models on the TypeScript side are combined into a single entry point, which is compiled by ESBuild and loaded by the Python `Map` class. (Refer to the `_esm` key on the `Map` class, which tells Jupyter/ipywidgets where to load the JavaScript bundle.)

Anywidget and its dependency ipywidgets handles the serialization from Python into JS, automatically keeping each side in sync.

## Publishing

Push a new tag to the main branch of the format `v*`. A new version will be published to PyPI automatically.

## Contribute

We run linting and formating on all pull requests. You can perform that operation locally with `pre-commit`.
```
pip install -U pre-commit
pre-commit run --all-files
```

## Documentation website

The documentation website is generated with `mkdocs` and [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material). After `poetry install`, you can serve the docs website locally with

```
poetry run mkdocs serve
```

Publishing documentation happens automatically via CI when a new tag is published of the format `v*`. It can also be triggered manually through the Github Actions dashboard on [this page](https://github.com/developmentseed/lonboard/actions/workflows/deploy-mkdocs.yml). Note that publishing docs manually is **not advised if there have been new code additions since the last release** as the new functionality will be associated in the documentation with the tag of the _previous_ release. In this case, prefer publishing a new patch or minor release, which will publish both a new Python package and the new documentation for it.

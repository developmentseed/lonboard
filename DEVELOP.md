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

The JavaScript dependencies are managed in `package.json` and tracked with Yarn or NPM (I haven't been consistent at using one or the other :sweat_smile:).

ESBuild is used for bundling into an ES Module that the Jupyter Widget loads at runtime. The ESBuild configuration is in `build.mjs`. You can run the script with

```
yarn build
```

I often run

```
fswatch -o src | xargs -n1 -I{} yarn build
```

to watch the `src` directory and run `yarn build` anytime it changes.

Currently, each Python model (the `ScatterplotLayer`, `PathLayer`, and `SolidPolygonLayer` classes) use _their own individual JS entry points_. You can inspect this with the `_esm` key on each class, which is used by anywidget to load in the widget. The ESBuild script converts `scatterplot-layer.tsx`, `path-layer.tsx`, and `solid-polygon-layer.tsx` into bundles used by each class, respectively.

Anywidget and its dependency ipywidgets handles the serialization from Python into JS, automatically keeping each side in sync.

## Publishing

Push a new tag to the main branch of the format `v*`. A new version will be published to PyPI automatically.

## Documentation website

The documentation website is generated with `mkdocs` and [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material). After `poetry install`, you can serve the docs website locally with

```
poetry run mkdocs serve
```

and you can publish the docs to Github Pages with

```
poetry run mkdocs gh-deploy
```

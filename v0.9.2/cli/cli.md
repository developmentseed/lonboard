# Command-line Interface

Lonboard includes a command-line interface for quickly viewing local data files.

The CLI is accessible either through the `lonboard` entry point or via `python -m lonboard` the latter can be useful to ensure that the `lonboard` instance you're calling is the same as your current `python` environment.

```
> lonboard --help
Usage: lonboard [OPTIONS] [FILES]...

  Interactively visualize geospatial data using Lonboard.

  This CLI can be used either to quickly view local files or to create static
  HTML files.

Options:
  -o, --output PATH   The output path for the generated HTML file. If not
                      provided, will save to a temporary file.
  --open / --no-open  Whether to open a web browser tab with the generated
                      map. By default, the web browser is not opened when
                      --output is provided, but is in other cases.
  --help              Show this message and exit.
```

For example:

```
lonboard data.geojson
```

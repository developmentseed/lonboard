# Using in pyodide

As of Lonboard version 0.10, it's possible to use Lonboard in [Pyodide](https://pyodide.org/en/stable/), where Python is running _inside your web browser_ in WebAssembly.

[![](../assets/lonboard-jupyterlite.png)][Jupyterlite demo]

[**Demo notebook**][Jupyterlite demo].

[Jupyterlite demo]: https://jupyterlite.ds.io/lab/index.html?path=lonboard%2Fdata-filter-extension.ipynb

There's a few things to keep in mind:

### Pyodide-specific dependencies

Not all Python libraries work out of the box in Pyodide. Any Python libraries that use compiled code need to be loaded in Pyodide with special wheels.

Lonboard does not use compiled code itself, but some of its dependencies — namely [`arro3`](https://github.com/kylebarron/arro3) — use compiled code. You may need to manually load `arro3` wheels before importing `lonboard`. Refer to the demo notebook for an example.

### Memory limits

Pyodide has stricter memory limits than normal Python environments. Take care to delete Python objects you're no longer using with `del`.

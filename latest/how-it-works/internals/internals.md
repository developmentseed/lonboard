# Internal Architecture

> Last edited April 2024.

This document will outline Lonboard's internal architecture, and hopefully should be useful for potential contributors.

## Pydeck

Before we consider Lonboard, we should briefly cover how Pydeck manages data transit.

<!-- It's impossible to consider Lonboard's architecture in isolation because many of Lonboard's architectural decisions were chosen in explicit contrast to pydeck. Lonboard and pydeck both bind to deck.gl, but have significantly different APIs and characteristics. -->

Pydeck uses the loaders.gl ecosystem natively supported in deck.gl. This means that pydeck passes the user input directly into the `data` prop of any given layer. When `data` is a string, it's interpreted as a URL, passed into loaders.gl machinery to parse the given data format to a list of GeoJSON features. In order to do data-driven styling, users pass in strings like `"@@=properties.valuePerSqm"` to describe the JavaScript callback that should be applied to each GeoJSON feature.

In my opinion, this presents performance pitfalls and gives Pydeck a stifling amount of flexibility. The Python API isn't able to do much of anything because the user input could be _anything_ and users end up writing a sort of JavaScript in Python strings.

## Lonboard

### Goals and target user persona

While I was never a primary pydeck developer and can't speak to their goals, I can say that Lonboard has a well-formed idea of the target user.

When I was learning geospatial data processing in Python, I learned that GeoPandas, Shapely, and others were amazing tools. But I would perform operations and not have a _deep understanding_ of what the output looked like. I wanted some way to quickly get a picture of what my data looked like. This drove me to build [`keplergl_cli`](https://github.com/kylebarron/keplergl_cli), a single function or CLI command to visualize data in an interactive HTML map. The desire for this simplicity lives on in Lonboard's `viz` function.

This experience informs the target user of Lonboard:

- A Python user who does not know or want to know JavaScript.
- Wants fast exploratory data analysis.
- Already working with data in Python.
- A reasonably fast internet connection on a desktop computer.

### Python classes

The `Map` class is the primary and only widget associated with JavaScript that renders anything. `Map` subclasses from `anywidget.AnyWidget`, which dynamically fetches Lonboard's JavaScript ESM bundle. The `Map` class emulates deck.gl's `Deck` class. It synchronizes map state and can be passed a sequence of `Layer` objects.

`Layer` classes are designed to map to each underlying deck.gl layer. Most `Layer` classes subclass from `BaseArrowLayer`, which stores a `pyarrow.Table` in the dataclass. This data object gets serialized to Parquet and rendered in a layer provided by `@geoarrow/deck.gl-layers` as described later on. The primary API for each of these Arrow-based layers is `from_geopandas`, which converts a `GeoDataFrame` to a `pyarrow.Table` with a [GeoArrow](https://geoarrow.org/)-represented geometry column. A few layers are not Arrow-based and do not subclass from `BaseArrowLayer`: primarily `BitmapLayer` and `BitmapTileLayer`. These pass user data input directly into a core deck.gl layer.

These `Layer` classes subclass from `ipywidgets.Widget` but are _not_ associated with any JavaScript of their own. But by being widgets themselves, their data is synced with JavaScript and Python data changes are propagated as events to the core `Map` object.

Each layer has parameters that map to deck.gl accessors and render properties. Each of these has validation on the Python side to catch invalid input early. Accessors are modeled with ["trait" objects](https://developmentseed.org/lonboard/latest/api/traits/). Scalar accessors are stored as a scalar int/string/float. Function accessors are evaluated in Python and stored as a `pyarrow.Array`.

A variety of [layer extensions](https://developmentseed.org/lonboard/latest/api/layer-extensions/) are supported, which map to deck.gl's upstream layer extensions. These layer extensions dynamically add more parameters to the layers on which they're assigned.


### Data loading

While pydeck allows users to pass in URLs to remote files, at the moment this is not possible in Lonboard. With only a few exceptions (e.g. the `BitmapLayer` and `BitmapTileLayer`), _only_ data originating in Python is supported in Lonboard. This reduction in scope vastly simplifies Lonboard's internals while not providing much of a hurdle for Lonboard's core audience.

Jupyter provides a WebSocket connection between Python and JavaScript. Jupyter widget state from Python classes is serialized over this WebSocket and received in JavaScript. While most widgets synchronize objects through JSON, widgets fully support binary data as well, which Lonboard utilizes.

#### Simplicity of code

Supporting only a single data provenance and format makes the internals of Lonboard much more maintainable. Lonboard's JavaScript bindings only need to include a single data parser and can optimize performance for Parquet and Arrow data.

#### Parquet

Parquet was chosen as the underlying data transmission format for its excellent compression, fast read and write speeds, compatibility with GeoArrow and, in turn, compatibility with deck.gl's binary API.

I tested with data from the speed test example (3 million points). Saving GeoArrow to Parquet was 135x faster than saving a GeoDataFrame to GeoJSON. The resulting file was 26x smaller. And parsing the Parquet to Arrow on the frontend was 5.6x faster than `JSON.parse` (including moving the Arrow from WebAssembly to JS).

Note that what is sent over the wire is _not_ GeoParquet. GeoParquet 1.0 requires special metadata and WKB-encoded geometries. Using that would require code on the frontend to parse WKB-encoded geometries into GeoArrow. The upcoming GeoParquet 1.1 includes support for GeoArrow but only its "separated" coordinates, where `x` and `y` coordinate values are in two different buffers (i.e. `xxxx`, `yyyy`). deck.gl's binary API currently does not support passing separated coordinates. Therefore Lonboard uses the "interleaved" coordinate variant, where `x` and `y` coordinates are stored in the same buffer (i.e. `xyxyxyxy`).


#### Bootstrapping GeoArrow

For performance reasons, Lonboard is very focused on using GeoArrow throughout the pipeline in both Python and JavaScript. At the time when Lonboard was started, there were no user-friendly tools for converting data to GeoArrow in client-side JavaScript. By supporting only data from Python and only Parquet data, we could focus on making data conversions from GeoPandas to GeoArrow in Python efficient and stable. This enables GeoArrow to be "just an implementation detail" and out of any primary public APIs while also working to bootstrap a GeoArrow ecosystem in Python and JavaScript.

#### Authentication

Since all data is loaded via Python over the Jupyter-provided WebSocket, Lonboard doesn't need to implement any sort of authentication itself. The user is able to use whatever credentials they're familiar with, say for S3, to access data. Those credentials never need to be passed to the browser.

In contrast, having the JavaScript side load data directly from a URL requires some way for users to specify authorization headers or API keys for access to private datasets.

### Layer Creation

With the exception of the `BitmapLayer`, no _direct_ deck.gl layers are used. deck.gl layers are used _exclusively_ through the [`@geoarrow/deck.gl-layers`](https://github.com/geoarrow/deck.gl-layers) glue library. This library connects GeoArrow data to the low-level binary data API of each deck.gl layer. **All** accessors are passed in directly as binary buffers.

This means that in JavaScript the data _never_ leaves an Arrow binary representation. It's parsed from Parquet to Arrow in WebAssembly, the Arrow buffers are copied out of WebAssembly memory, but never parsed to JSON strings or JavaScript objects.

### Accessors and data-driven rendering

Loading data from Python also helps to simplify data-driven rendering.

#### No function serialization

If we can make the data movement between Python and JavaScript fast enough, we can serialize _computed rendering properties_ rather than the function to generate them. Lonboard serializes data, not functions.

Any accessor used to style data is computed in Python, stored as a binary array, serialized to Parquet and sent to the frontend. Other than parsing the input Parquet buffers to Arrow, no data transformations or modifications are done on the JavaScript side.

In Pydeck users had to pass something like

```py
getRadius="@@=properties.valuePerSqm"
```

which would be expanded into

```js
getRadius: (object) => object.properties.valuePerSqm
```

on the JavaScript side.

I find this syntax to be horrible UX. The user is no longer writing Python, they need to learn a new DSL just for this.

RGB Colors for 3 million points take up 9MiB in memory (or 12MiB for RGBA). In the example of speed test data, 12MiB of RGBA data compressed down to 4MiB for transit. Float32 radii values for 3 million points take up 12MiB in memory and 9MiB compressed.

Even for users on remote Python environments, this takes no more than a couple seconds to download, and then can render almost instantly. For non-point datasets with a fewer number of geometries, the byte size of accessors are even smaller relative to the geometry buffers.

#### Update styling without re-sending data

With Lonboard's widget architecture, any accessors other than the geometry are stored separately to the main Arrow table. This means that all accessors and rendering properties can be updated in isolation. The core table does not need to be synced again when a property is updated.

#### Uses familiar objects

Accessors are defined in terms of Numpy arrays, Pandas Series or PyArrow Arrays, which are familiar to Python data scientists.

#### Full access to Python

Because we serialize _data_ to JavaScript instead of a function in a custom DSL, the user has the full spectrum of Python available to them. They can use one of matplotlib's many [normalization helpers](https://matplotlib.org/stable/api/_as_gen/matplotlib.colors.Normalize.html) before [applying a colormap](https://developmentseed.org/lonboard/latest/api/colormap/#lonboard.colormap.apply_continuous_cmap). Or they can use apply some ML model and use its outputs for point radii.

# How it works?


Lonboard is built on four foundational technologies: deck.gl, GeoArrow, GeoParquet, and anywidget.

- [deck.gl](https://deck.gl/) is a JavaScript geospatial data visualization library. Because deck.gl uses the GPU in your computer to render data, it's capable of performantly rendering very large quantities of data.
- [GeoArrow](https://geoarrow.org/) is a memory format for efficiently representing geospatial vector data. As a memory format, GeoArrow is not compressed and can be used directly.
- [GeoParquet](https://geoparquet.org/) is a file format for efficiently encoding and decoding geospatial vector data. As a file format, GeoParquet contains very efficient compression, and needs to be parsed before it can be used. [^1]
- [anywidget](https://anywidget.dev/) is a framework for building custom Jupyter widgets that makes the process much easier than before.

[^1]: For subtle technical reasons, Lonboard's internal data transfer doesn't match the exact GeoParquet specification. Lonboard uses the highly-efficient GeoArrow encoding inside of GeoParquet instead of storing geometries as Well-Known Binary (WKB). While the GeoParquet 1.1 spec does support a "native" GeoArrow-like encoding, note that GeoArrow defines two [_coordinate layouts_](https://geoarrow.org/format.html#coordinate): "separated" and "interleaved". Only "separated" is allowed in the GeoParquet spec because only the "separated" layout generates useful column statistics to be used for cloud-native spatial queries. However, deck.gl expects the "interleaved" layout. So Lonboard prepares Arrow data in that exact format to avoid an extra memory copy on the JavaScript side before uploading to the GPU.

## How is it so fast?

Lonboard is so fast because it moves data from Python to JavaScript (in your browser) and then from JavaScript to your Graphics Processing Unit (GPU) more efficiently than ever before.

Other Python libraries for interactive maps exist (such as [`ipyleaflet`](https://github.com/jupyter-widgets/ipyleaflet)), and even existing bindings to deck.gl exist (such as [`pydeck`](https://pypi.org/project/pydeck/)). But those libraries encode data as GeoJSON to copy from Python to the browser. GeoJSON is **extremely slow** to read and write and results in a very large data file that has to be copied to the browser.

With lonboard, the _entire pipeline_ is binary. In Python, GeoPandas to GeoArrow to GeoParquet avoids a text encoding like GeoJSON and results in a compressed binary buffer that can be efficiently copied to the browser. In JavaScript, GeoParquet to GeoArrow offers efficient decoding ([in WebAssembly](https://github.com/kylebarron/parquet-wasm/)). Then deck.gl is able to interpret the GeoArrow table _directly_ without any parsing (thanks to [`@geoarrow/deck.gl-layers`](https://github.com/geoarrow/deck.gl-layers)).

[GeoPandas](https://geopandas.org/en/stable/) is the primary interface for users to add data, allowing lonboard to internally manage the conversion to GeoArrow and its transport to the browser for rendering.

Lonboard's goal is to abstract the technical bits of representing and moving data so it can attain its dual goals of performance and ease of use for a vast audience.

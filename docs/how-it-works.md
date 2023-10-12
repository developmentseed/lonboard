# How it works?


Lonboard is built on four foundational technologies: deck.gl, GeoArrow, GeoParquet, and anywidget.

[deck.gl](https://deck.gl/) is a JavaScript geospatial data visualization library. Because deck.gl uses the GPU in your computer to render data, it's capable of performantly rendering very large quantities of data.

[GeoArrow](https://geoarrow.org/) is a memory format for efficiently representing geospatial vector data. As a memory format, GeoArrow is not compressed and can be used directly.

[GeoParquet](https://geoparquet.org/) is a file format for efficiently encoding and decoding geospatial vector data. As a file format, GeoParquet contains very efficient compression, and needs to be parsed before it can be used. [^1]

[^1]: lonboard currently doesn't use "official" GeoParquet 1.0, because the 1.0 spec requires encoding geometries as Well-Known Binary (WKB) inside of the Parquet file. lonboard uses the highly-efficient GeoArrow encoding inside of GeoParquet (which may [become part of the GeoParquet spec in 1.1](https://github.com/opengeospatial/geoparquet/issues/185)). This is faster and easier to write when the writer and reader are both using GeoArrow anyways.

[anywidget](https://anywidget.dev/) is a framework for building custom Jupyter widgets that makes the process much easier than before.

## How is it so fast?

Lonboard is so fast because it moves data from Python to JavaScript (in your browser) and then from JavaScript to your Graphics Processing Unit (GPU) more efficiently than ever before.

Other Python libraries for interactive maps exist (such as [`ipyleaflet`](https://github.com/jupyter-widgets/ipyleaflet)), and even existing bindings to deck.gl exist (such as [`pydeck`](https://pypi.org/project/pydeck/)). But those libraries encode data as GeoJSON to copy from Python to the browser. GeoJSON is **extremely slow** to read and write and results in a very large data file that has to be copied to the browser.

With lonboard, the _entire pipeline_ is binary. In Python, GeoPandas to GeoArrow to GeoParquet avoids a text encoding like GeoJSON and results in a compressed binary buffer that can be efficiently copied to the browser. In JavaScript, GeoParquet to GeoArrow offers efficient decoding ([in WebAssembly](https://github.com/kylebarron/parquet-wasm/)). Then deck.gl is able to interpret the GeoArrow table _directly_ without any parsing (thanks to [`@geoarrow/deck.gl-layers`](https://github.com/geoarrow/deck.gl-layers)).

The end user doesn't care about rendering _GeoJSON_, they want to render _their data_. Lonboard focuses on abstracting how to most efficiently move data so that the end user doesn't have to think about it.

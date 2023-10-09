# Alternatives to Lonboard

## Lonboard vs ipyleaflet

[ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) is a great rendering library for small- and medium-sized datasets. ipyleaflet supports a broad range of data types and formats and gives the user broad control over how to render data.

The downside of ipyleaflet is that it doesn't support large datasets as well. It uses GeoJSON to transfer data to the frontend, which is slow to write, slow to read, and large in transit. Additionally, leaflet's primary goal is not to support very large quantities of data.

## Lonboard vs pydeck

[Pydeck](https://deckgl.readthedocs.io/en/latest/) is a full-featured binding from Python to deck.gl. Pydeck attempts to cover most of the deck.gl API. It's harder to use binary data transport with pydeck, and similarly to ipyleaflet will usually serialize data to GeoJSON.

Lonboard does not try to cover deck.gl's _full_ API, but rather has an opinionated approach that nudges users to the fastest rendering for many common use cases.

## Lonboard vs datashader

[Datashader](https://datashader.org/) is a truly _scalable_ rendering library. Datashader will re-render your data from scratch when panning around in a map. This allows datashader to _aggregate_ the source data before rendering. Datashader _minimizes the amount of data being rendered_ and thus, in theory, Datashader should perform well for datasets as large as your computer's memory.

Lonboard is not scalable in the same sense. It doesn't minimize the amount of data being rendered. If you ask to plot a GeoDataFrame with 3 million points, every single one of those points is transferred to the GPU and drawn to your screen. In contrast to Datashader, Lonboard should perform well for datasets whose geometries fit in your computer's _**GPU memory**_, which is usually much smaller than your computer's total memory.

---
draft: false
date: 2026-04-02
categories:
  - Release
  - Feature
authors:
  - kylebarron
# links:
#     # TODO: update changelog link
#   - CHANGELOG.md#0130-2025-11-05
---

# Cloud-Optimized GeoTIFFs in Lonboard

[![](../../assets/initial-cog-blog-hero.jpg)][nlcd_cog_example]

[nlcd_cog_example]: ../../../../../examples/raster-cog-nlcd-server

We've added support for rendering [Cloud-Optimized GeoTIFF]s (COGs) in Lonboard.

It works out of the box with the [vast majority](#most-cloud-optimized-geotiffs-supported) of COG data in the wild. COG tiles are streamed on demand as required, letting you visualize massive multi-gigabyte files on the fly.

You have full customizability of how image data is displayed. No need to set up a separate tile server. No need to download full images. No dependency on GDAL.

[Cloud-Optimized GeoTIFF]: https://cogeo.org/

<!-- more -->

## Overview

The [`RasterLayer`][lonboard.RasterLayer] now has a [`from_geotiff`][lonboard.RasterLayer.from_geotiff] constructor. Use this to visualize a [GeoTIFF][async_geotiff.GeoTIFF] object from the [Async-GeoTIFF] library.

Three simple steps:

1. Open a [`GeoTIFF`][async_geotiff.GeoTIFF] using [Async-GeoTIFF] and [Obstore].
2. Create a _render function callback_ — `render_tile` — for converting NumPy array data loaded from the GeoTIFF to a PNG image. This gives you full control for how you want to visualize the GeoTIFF image data
3. Pass both of the above into [`RasterLayer.from_geotiff`][lonboard.RasterLayer.from_geotiff] and, voilà! Your COG is rendering on the map!

[Async-GeoTIFF]: https://developmentseed.org/async-geotiff/latest/
[Obstore]: https://developmentseed.org/obstore/latest/

## Example


## Features

### Most Cloud-Optimized GeoTIFFs supported

This initial release supports the vast majority of COGs you might find in the wild. Some primary exceptions are COGs that:

- Cross the antimeridian
- Use a polar projection
- Have a rotated affine transformation
- Have non-square pixels

Each of these are pretty uncommon, and in any case we plan to be fixed in an upcoming release.

### No need to deploy/host a tile server

The Lonboard COG support works with any file that you can access with Async-GeoTIFF, whether it's a local file on disk or behind cloud storage authentication. As long as you can access a COG with Async-GeoTIFF, Lonboard can stream and visualize it directly, even if there's no public URL to access it.

With the `render_tile` callback, you're effectively creating your own tile server through Lonboard. As you pan around the map, Lonboard automatically calls `render_tile`, as it fetches more data from the COG.

This is akin to what a tile server like [Titiler] is doing, but this happens in your own Python environment instead of deploying a separate server. But unlike Titiler, no raster warping is needed because reprojection happens automatically in the browser.

In the future, we'll add support for client-side, GPU-based visualization, allowing for richer visualization options. See [Future Work](#future-work).

[Titiler]: https://github.com/developmentseed/titiler

## How it works





### Building on deck.gl-raster

For the last few months I've been working on [deck.gl-raster], a new extension library for [deck.gl] that supports generically visualizing COG data.  Since Lonboard is built upon deck.gl, we can seamlessly integrate deck.gl-raster into Lonboard.

deck.gl-raster takes care of the tile selection and image reprojection. As you pan around the map, deck.gl-raster integrates with the deck.gl [`TileLayer`] to fetch more data from the COG as necessary.

Then, when image data for each tile arrives in the client, deck.gl-raster manages client-side reprojection from the source projection into Web Mercator.

[deck.gl]: https://deck.gl/
[deck.gl-raster]: https://developmentseed.org/deck.gl-raster/
[`TileLayer`]: https://deck.gl/docs/api-reference/geo-layers/tile-layer


### Python as a simple data proxy

This implementation relies heavily on [Async-GeoTIFF]. In fact **all data fetching is happens through Python**. The browser has no direct connection to the COG and is not fetching any image data directly; the _only_ things known by the client are the layout of the COG tile grid and how to ask Python for more tiles.

- When you pan the map, deck.gl and deck.gl-raster decide which COG tiles should be loaded for the current viewport.
- Lonboard's TypeScript code interprets those tile requests and forwards on a request to Python for each one.
- In turn, Lonboard's Python code calls [`GeoTIFF.fetch_tile`][async_geotiff.GeoTIFF.fetch_tile] to asynchronously fetch data for each tile index.
- When [`GeoTIFF.fetch_tile`][async_geotiff.GeoTIFF.fetch_tile] has finished loading a tile,
- The browser requests a tile from Python, which in turn requests a tile over the network. This is why the underlying cog client really had to be async. In order to get data fetching performance the end user expects, we couldn't use rasterio. Even if we were running rasterio in a thread pool (which is hard to do, only really possible for geotiff in specific situations, depends on the underlying gdal version if you want to use the libertiff driver, etc (link to stack stac)) it would probably have significantly slower performance than async-geotiff.

But why fetch data through Python instead of directly from the browser? A couple reasons:

### Simpler Authentication

For one, authentication. A general premise of lonboard is that users are already working with data in python and want to better understand that data through visualization. This implies that the user is already able to access the data in python, somehow.

But it's not generally possible to "serialize authentication" from Python into JavaScript. Just because Python has access to a COG doesn't mean the browser environment will also. Often user data is not publicly accessible. Accessing data on cloud storage might require calling vendor-specific sdks in the browser, which is tricky. Furthermore, passing credentials into the browser could have security implications. In some situations, if there were malicious browser extensions, the cloud storage credentials could be compromised.

By leaving all data fetching to python and then proxying data responses into the browser, we can have a single, reliable value proposition: **if you can load it in python, you can visualize it in lonboard**.

### Customize visualizations with Python code

Second, a core value proposition of lonboard is that you should be able to use **any Python code** to control your visualization. Pydeck, a predecessor, also implemented bindings to deckgl but it tried to serialize only the data and apply styling on the js side. This meant that you had to write complex strings representing JavaScript expressions that would be evaluated on your json data. Apart from being very hard to maintain on the pydeck side, and apart from being hard to safely execute untrusted JavaScript code, it was a horrible user API. **Python users want to be able to write Python code and whatever existing Python libraries they're familiar with**.

By proxying cog data through Python, we can maintain that same value proposition for raster data too. If you want to use Python to style your COG data, you can use python to style your COG data. Pass any sort of Python callback you'd like, as long as it returns an RGB array of data that the frontend can visualize.

In the future we have plans for exciting new ways to customize rendering on the webgl side, but for now the python side gives you options.



### The crucial importance of async-geotiff

Relying on async-geotiff will also hopefully show more end users the benefits of async data loading, which might get more people interested in async-geotiff.

This approach would be impossible with rasterio because each tile request from JavaScript would block the main thread in Python while waiting for the rasterio requests to finish.

In fact, it was the goal of providing COG support in Lonboard that really drove my desire to get Async-GeoTIFF to a production-ready state.

## Future Work

### Zarr integration

Soon we'll start work in deck.gl-raster on integrating with [GeoZarr] to generically support Zarr visualizations in the browser. Once completed, we can connect Lonboard to [Zarr-Python] datasets as well as COGs.

[GeoZarr]: https://geozarr.org/
[Zarr-Python]: https://zarr.readthedocs.io/en/stable/

### Client-side rendering

Today's release sets the groundwork for rendering COGs in Lonboard, but rendering is still "server-side" in your `render_tile` callback.

In the future, you'll be able to pass raw GeoTIFF data to the browser to customize rendering on the fly, apply pixel filtering dynamically, and animate over time series.

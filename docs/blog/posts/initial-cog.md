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

1. [Open a `GeoTIFF`][async_geotiff.GeoTIFF.open] using [Async-GeoTIFF] and [Obstore].
2. Create a _render function_ that converts [`Tile`s][async_geotiff.Tile] loaded on demand from the GeoTIFF to PNG, JPEG, or WebP images. This gives you full control for how you want to render the image data.
3. Pass the `GeoTIFF` and the render function (as the `render_tile` parameter) to [`RasterLayer.from_geotiff`][lonboard.RasterLayer.from_geotiff] and, voilà! Your COG is on the map!

[Async-GeoTIFF]: https://developmentseed.org/async-geotiff/latest/
[Obstore]: https://developmentseed.org/obstore/latest/

## Features

### Visualize massive COGs on demand

There's no restriction to the size of COGs that you can visualize with the `RasterLayer`. COG tiles will be streamed as necessary depending on your map's viewport.

The [Land Cover example notebook][nlcd_cog_example] visualizes a 1.3GB COG on the fly with no hiccups.

### Full control over image rendering

Use any Python code — with _any_ dependencies you'd like — to customize how your images are displayed.

Use NumPy to customize band combinations and apply colormaps. Or for, say, embeddings data, you might want to apply some Machine Learning model on the fly as tiles are rendered.

For now Lonboard requires you to define the rendering as a Python callback, but [in the future](#future-work), we'll add support for client-side, GPU-based visualization. This will allow for richer visualizations, like dynamic pixel filtering, client-side band math, and animation over time series.

### Any COG, anywhere

Any COG that you can access with [Async-GeoTIFF] you can visualize. You're not limited to publicly accessible data; local files and private data behind authentication work seamlessly, even when no public URL exists to access it.

Any credentials you use to load files never leave your Python environment and aren't transferred to the browser session.

### No need to deploy and host a tile server

With the [`render_tile` callback][lonboard.RasterLayer.from_geotiff], you're effectively creating your own tile server through Lonboard. As you pan around the map, Lonboard automatically calls `render_tile` as it fetches more data from the COG.

This is akin to what a tile server like [Titiler] is doing, but this happens in your own Python environment instead of deploying a separate server. And unlike Titiler, no raster warping is needed because reprojection happens automatically in the browser.

[Titiler]: https://github.com/developmentseed/titiler

### Most Cloud-Optimized GeoTIFFs supported

This initial release supports the vast majority of COGs you might find in the wild. Some primary exceptions are COGs that:

- Cross the antimeridian.
- Use a polar projection.
- Have a rotated affine transformation.
- Have non-square pixels.

Each of these are pretty uncommon, and in any case we plan to be fixed in an upcoming release.

## Example

There are full notebook examples for how to render [Land Cover][nlcd_cog_example] and [RGB COGs with an alpha mask][raster-cog-rgb-server], but here we'll start with the simplest example of rendering an RGB COG without a nodata value or alpha mask.

[raster-cog-rgb-server]: ../../../../../examples/raster-cog-rgb-server

This example plots an RGB COG from the [New Zealand Imagery AWS Open Data bucket](https://registry.opendata.aws/nz-imagery/), provided by [Land Information New Zealand].

[Land Information New Zealand]: https://www.linz.govt.nz/

```py
import io

from async_geotiff import GeoTIFF, Tile
from async_geotiff.utils import reshape_as_image
from obstore.store import S3Store
from PIL import Image

from lonboard import Map, RasterLayer
from lonboard.raster import EncodedImage

# Create a new Obstore S3Store mounted to our desired bucket
store = S3Store("nz-imagery", region="ap-southeast-2", skip_signature=True)

# Open a GeoTIFF instance
cog_path = "new-zealand/new-zealand_2024-2025_10m/rgb/2193/CC11.tiff"
geotiff = await GeoTIFF.open(cog_path, store=store)


# Define our render callback. It must return an instance of `EncodedImage`.
def render_tile(tile: Tile) -> EncodedImage:
    """Convert the array data from the GeoTIFF to an RGB PNG."""

    # Reshape from (bands, height, width) to (height, width, bands)
    image_array = reshape_as_image(tile.array.data)

    # For some COGs you may need more logic here to convert pixel data to RGB,
    # but in this case our data is already RGB

    # Encode as PNG, in this case using PIL
    img = Image.fromarray(image_array)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return EncodedImage(data=buf.getvalue(), media_type="image/png")

# Create a RasterLayer and put it on a map
layer = RasterLayer.from_geotiff(geotiff, render_tile=render_tile)
m = Map(layer)
m
```

Voilà here's the COG displayed:

![](../../assets/initial-cog-example.jpg)

### Debugging `render_tile`

If you're having problems with `render_tile` raising exceptions (which should print in red below the map instance) or the COG isn't rendering as you expect, you can debug `render_tile` in isolation.

First, use [`GeoTIFF.fetch_tile`][async_geotiff.GeoTIFF.fetch_tile] to load one tile from your GeoTIFF into memory. In this case, we load the top-left tile from the COG.

```py
tile = await geotiff.fetch_tile(0, 0)
```

Now, pass the `tile` into your `render_tile` callback:

```py
render_tile(tile)
```

The result of `render_tile` (which must be an [`EncodedImage`][lonboard.raster.EncodedImage]) should automatically display.

![](../../assets/raster-tile-debug.jpg)

## How it works





### Building on deck.gl-raster

For the last few months I've been working on [deck.gl-raster], a new extension library for [deck.gl] that supports generically visualizing raster data like COG (and soon Zarr). Since Lonboard is built upon deck.gl, we can seamlessly integrate deck.gl-raster into Lonboard.

deck.gl-raster takes care of the tile selection and image reprojection. As you pan around the map, deck.gl-raster uses the deck.gl [`TileLayer`](https://deck.gl/docs/api-reference/geo-layers/tile-layer) to fetch more data from the COG as necessary.

Then, when image data for each tile arrives in the client, deck.gl-raster manages client-side reprojection from the source projection into Web Mercator.

[deck.gl]: https://deck.gl/
[deck.gl-raster]: https://developmentseed.org/deck.gl-raster/

### Async-GeoTIFF as a basic data proxy

This implementation relies heavily on the [Async-GeoTIFF] Python library. In fact **all data fetching happens through Python**. The browser has no direct connection to the COG and does not fetch any image data directly; the _only_ things known by the client are the layout of the COG tile grid and how to ask Python for more tiles.

- When you pan the map, deck.gl and deck.gl-raster decide which COG tiles should be loaded for the current viewport.
- Lonboard's frontend code forwards those tile requests on to Python using the [Jupyter communication mechanism](https://jupyter-client.readthedocs.io/en/latest/messaging.html#).
- Lonboard's Python code calls [`GeoTIFF.fetch_tile`][async_geotiff.GeoTIFF.fetch_tile] to _asynchronously_ fetch data for each tile index.
- When [`GeoTIFF.fetch_tile`][async_geotiff.GeoTIFF.fetch_tile] has finished loading a tile, that's passed as input to the user's `render_tile` function.
- The result of `render_tile` is passed _back_ to the frontend via Jupyter and rendered to screen with deck.gl and deck.gl-raster.

But why fetch data through Python instead of directly from the browser? A couple reasons:

### Simpler Authentication

A general premise of Lonboard is that users are already working with data in Python and want to better understand that data through visualization. This implies that the user is already able to access the data in Python.

But it's not generally possible to "serialize authentication" from Python into JavaScript. Just because Python has access to a COG doesn't mean the browser environment can also access it.

Often, user data is not publicly accessible. There's no easy way for the browser to directly access local files, especially when the Jupyter session is running on a remote machine. And having the browser directly access private cloud storage buckets would require depending on vendor-specific SDKs in the browser, which is tricky, adds complexity, and grows the bundle size.

Furthermore, passing credentials into the browser could have security implications. In some situations, such as with malicious browser extensions, the cloud storage credentials could be compromised.

By leaving all data fetching to Python and then proxying tiles into the browser, we can maintain Lonboard's first core value proposition: **if you can load it in Python, you can visualize it in Lonboard**.

### Customize rendering with pure Python

Lonboard's second core value proposition: **you should be able to use any Python code with any dependency you want to control your visualization**.

In the context of vector data, [Pydeck], a predecessor binding to deck.gl, tried to serialize the raw input data to the browser and apply styling on the frontend side. This required users to write complex strings representing JavaScript expressions. Apart from being a horrible user API, this was hard to maintain and ensure that untrusted JavaScript input was being executed safely.

[Pydeck]: https://deckgl.readthedocs.io/en/latest/

By proxying COG data through Python, we can maintain that same value proposition for raster data too. Pass any sort of Python callback you'd like, using any dependencies you'd like, as long as it returns a PNG that the frontend can visualize.

[In the future](#future-work) we'll add support for client-side rendering too, which will give you options over when to use Python-based or WebGL-based styling.

### The crucial importance of Async-GeoTIFF

The frontend sends many individual tile requests to Python, which means that we want to make many concurrent tile requests to the underlying GeoTIFF. And the Python code fetching those tiles is running _in the user's existing Python environment_.

So a blocking, synchronous loader like Rasterio would both completely stall the user's Python session _and_ those requests would be extremely slow as the second request wouldn't start until the first request finished. I don't _think_ it's possible to put Rasterio's tile fetches into a thread pool, unless perhaps you require opting-in to the new [libertiff driver](https://gdal.org/en/stable/drivers/raster/libertiff.html) in GDAL 3.11. Even then, it would be messy to manage a thread pool.

To get excellent performance here, the client that fetches the image tiles really **must be asynchronous**.

[Async-GeoTIFF] is a new high-level library for reading GeoTIFF and Cloud-Optimized GeoTIFF (COG) data. With a [Rust core](https://github.com/developmentseed/async-tiff) that exposes asynchronous GeoTIFF fetching to Python, it vastly speeds up concurrent GeoTIFF data fetching, like what we need in Lonboard.

By using Async-GeoTIFF, we can ensure that Lonboard's COG visualizations have the maximum possible performance. In fact, Lonboard integration was a driving factor to get Async-GeoTIFF to a production-ready state.

## Future Work

### Zarr integration

Soon we'll start work in deck.gl-raster on integrating with [GeoZarr] to generically support Zarr visualizations in the browser. Once completed, we can connect Lonboard to [Zarr-Python] datasets as well as COGs.

[GeoZarr]: https://geozarr.org/
[Zarr-Python]: https://zarr.readthedocs.io/en/stable/

### Client-side rendering

Today's release sets the groundwork for rendering COGs in Lonboard, but rendering is still "server-side" in your `render_tile` callback.

In the future, you'll be able to pass raw GeoTIFF data to the browser to customize rendering on the fly, apply pixel filtering dynamically, and animate over time series.

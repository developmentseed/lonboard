---
draft: false
date: 2026-02-12
categories:
  - Release
authors:
  - kylebarron
links:
  - CHANGELOG.md
---

# Releasing lonboard 0.14!

Lonboard is a Python library for fast, interactive geospatial data visualization in Jupyter.

This post gives an overview of what's new in Lonboard version 0.14.

<!-- more -->

Refer to the [changelog] for all updates.

## PMTiles Raster support

As the first step towards broader raster data integration, we now support visualizing raster PMTiles archives through Lonboard.

![](../../assets/pmtiles-raster.gif)

For example, using an [Obstore] `HTTPStore` to read a PMTiles file over HTTP:

[Obstore]: https://developmentseed.org/obstore/latest/

```py
from async_pmtiles import PMTilesReader
from lonboard import Map, RasterLayer
from obstore.store import HTTPStore

store = HTTPStore("https://air.mtn.tw")
reader = await PMTilesReader.open("flowers.pmtiles", store=store)
layer = RasterLayer.from_pmtiles(reader)
m = Map(layer)
```

The `RasterLayer` supports only raster-formatted PMTiles archives; it doesn't support those containing vector data.

## Category filtering in DataFilterExtension

This feature was contributed by @ATL2001.

## All updates

Refer to the [changelog] for all updates.

[changelog]: ../../CHANGELOG.md/#0140-2026-02-11

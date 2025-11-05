---
draft: false
date: 2025-11-05
categories:
  - Release
authors:
  - kylebarron
links:
  - CHANGELOG.md
---

# Releasing lonboard 0.13!

Lonboard is

This post gives an overview of what's new in Lonboard version 0.13.

<!-- more -->

Refer to the [changelog] for all updates.

It should have globe view, new layer types (h3, s2, geohash, a5, fixed heatmap layer), interleaved rendering with maplibre (so you can render data underneath basemap labels), map controls like scale/fullscreen/navigation, performance improvements,


## Globe view

## New layer types: H3, S2, Geohash, A5

Lonboard supports new layer types for [H3][h3], [S2][s2], [Geohash][geohash], and [A5][a5] data.

[h3]: https://h3geo.org/
[a5]: https://a5geo.org/
[s2]: http://s2geometry.io/
[geohash]: https://en.wikipedia.org/wiki/Geohash

- [`H3HexagonLayer`][lonboard.H3HexagonLayer]: render hexagons from the [H3][h3] geospatial indexing system
- [`S2Layer`][lonboard.S2Layer]: render polygons based on the [S2][s2] geospatial indexing system.
- [`A5Layer`][lonboard.A5Layer]: render polygons based on the [A5][a5] geospatial indexing system.
- [`GeohashLayer`][lonboard.GeohashLayer]: render polygons based on the [Geohash][geohash] geospatial indexing system.

![](../../assets/kontur-h3.jpg)

> Screenshot from [H3 Population](../../../../../examples/kontur_pop) example

Additionally, the [HeatmapLayer][lonboard.HeatmapLayer], which has been broken since Lonboard v0.10 due to upstream changes in deck.gl, has been fixed and is now functional again. (Thanks to @felixpalmer for [fixing this upstream](https://github.com/visgl/deck.gl/pull/9787)!).

## Interleaved rendering with Maplibre

When rendering dense visualizations, the data can obscure helpful elements of the basemap, removing spatial context from the visualization.

It's now possible to render Lonboard data layers interleaved in the Maplibre layer stack. This means Maplibre text labels can be rendered above your Lonboard-rendered data.

![](../../assets/interleaved-labels.jpg)

> Screenshot from [H3 Population](../../../../../examples/interleaved-labels) example

To do this:

- Set [`before_id`][lonboard.layer.BaseLayer.before_id] on your layer as the value of the Maplibre layer `id` you want the Lonboard layer to be under. See [`before_id`][lonboard.layer.BaseLayer.before_id] for more information.
- Create a new basemap [set to `interleaved` mode][lonboard.basemap.MaplibreBasemap.mode]:
- Pass the basemap to the `Map` constructor.

```py
from lonboard.basemap import MaplibreBasemap
from lonboard import Map, ScatterplotLayer

# Example layer ID when using Carto basemap styles
layer = ScatterplotLayer(..., before_id="watername_ocean")
basemap = MaplibreBasemap(mode="interleaved")
m = Map(layer, basemap=basemap)
```

## Map controls: scale, fullscreen, navigation

Common UI elements that we call "Controls" are now supported in Lonboard maps. In this release, this includes three types of controls:

- Scale control: shows a scale bar on the map
- Fullscreen control: button to toggle fullscreen mode
- Navigation control: zoom in/out buttons and a compass

These three controls are rendered on the map by default, but can be customized via the [`Map.controls`][lonboard.Map.controls] attribute. See [`lonboard.controls`][] for more information.

![](../../assets/controls-example.jpg)

## Performance improvements

First and foremost, I learned there was _severe bug_ in which the string representation (aka `repr`) of the [`table` attribute][lonboard.BaseArrowLayer.table] was being generated during map display. In conjunction with [an upstream issue](https://github.com/kylebarron/arro3/issues/432), this made it _very slow_ to render a map for datasets with many coordinates in a single row (such as polygons representing administrative boundaries). https://github.com/developmentseed/lonboard/pull/1015 **improved the Python-side of rendering by 99% in this case**, from 12 seconds to 5 milliseconds.

In https://github.com/developmentseed/lonboard/pull/902 we now fully parallelize the Parquet file generation in a thread pool on the Python side, leading to 4x faster Parquet serialization.

In https://github.com/developmentseed/lonboard/pull/954 we improve the Polygon rendering performance on the JavaScript side and remove a network request for a dependency needed to perform multi-threaded preparation for Polygon data rendering.

In general, Lonboard data rendering should feel instantaneous. If it's especially slow, on the order of ~10 seconds, [open an issue](https://github.com/developmentseed/lonboard/issues/new/choose) with your dataset to discuss.

## All updates

Refer to the [changelog] for all updates.

[changelog]: ../../CHANGELOG.md/#0130-2025-11-05

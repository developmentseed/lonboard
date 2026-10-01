---
draft: false
date: 2026-10-02
categories:
  - Release
authors:
  - kylebarron
links:
  - CHANGELOG.md#0170-2026-10-02
---

# Releasing lonboard 0.17!

> This blog post was fully human written.

Lonboard is a Python library for fast, interactive geospatial data visualization in Jupyter.

Lonboard version 0.17 has a ton of small improvements and bug fixes.

<!-- more -->

Refer to the [changelog] for all updates.

## DuckDB updates

### We now read CRS from DuckDB geometry columns

Starting from DuckDB version 1.5, DuckDB supports a [native geometry type](https://duckdb.org/docs/current/sql/data_types/geometry) that [tracks its coordinate reference system](https://duckdb.org/2026/03/09/announcing-duckdb-150#coordinate-reference-system-support).

Lonboard will automatically read that CRS and reproject to the target coordinate system.

See [#1205](https://github.com/developmentseed/lonboard/pull/1205) and [#1210](https://github.com/developmentseed/lonboard/pull/1210) for more information.

### Reading from DuckDB doesn't require PyArrow dependency

We no longer require PyArrow to be installed when reading from a DuckDB query. This uses the [Arrow PyCapsule Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html) to share Arrow data across Python libraries without needing PyArrow to serve as an intermediary.

See [#1303](https://github.com/developmentseed/lonboard/pull/1303) for more information.

## Pyodide/JupyterLite support to run inside your browser

[![Try it in JupyterLite][jupyterlite_badge]][jupyterlite_link]

[jupyterlite_badge]: https://jupyterlite.rtfd.io/en/latest/_static/badge.svg
[jupyterlite_link]: https://developmentseed.org/lonboard/jupyterlite/lab/index.html?path=getting-started.ipynb

Lonboard and all its (core) dependencies now support [Pyodide](https://pyodide.org/en/stable/) and [JupyterLite](https://github.com/jupyterlite/jupyterlite). It can run _entirely within your browser_ without having to install a Python interpreter on your machine.

See [our Pyodide documentation](../../ecosystem/pyodide.md) or [try it out in your browser][jupyterlite_link].

See [#1204](https://github.com/developmentseed/lonboard/pull/1204) and [#1320](https://github.com/developmentseed/lonboard/pull/1320) for more information.

## Programmatically set the time of a `TripsLayer`

Previously it was only possible to read the `current_time` property but not set it. Now it's possible to programmatically set and change the value as well.

See [#1308](https://github.com/developmentseed/lonboard/pull/1308) for more information.

## Breaking Changes

The `basemap_style` and `CartoBasemap` exports had been deprecated since 0.13.0 and are now removed. Use [MaplibreBasemap][lonboard.basemap.MaplibreBasemap] and [CartoStyle][lonboard.basemap.CartoStyle] instead.

These changes allow for better customization of basemaps and the option to remove a basemap entirely.

See [#1307](https://github.com/developmentseed/lonboard/pull/1307) for more information.

## Bug fixes

- Fix rendering polygons in exported HTML files [#1264](https://github.com/developmentseed/lonboard/pull/1264)
- Fix errors for empty record batch or geometry input [#1269](https://github.com/developmentseed/lonboard/pull/1269)
- Fix `RasterLayer.from_pmtiles` [#1274](https://github.com/developmentseed/lonboard/pull/1274)
- Remove upper bound on anywidget dependency [#1282](https://github.com/developmentseed/lonboard/pull/1282)
- Support boolean data in `apply_categorical_cmap` [#1300](https://github.com/developmentseed/lonboard/pull/1300)
- Reset example notebook kernelspec to python3 [#1254](https://github.com/developmentseed/lonboard/pull/1254)
- Show the map controls on deck-first maps [#1309](https://github.com/developmentseed/lonboard/pull/1309)
- Set selected_index to the row's position in the whole table [#1283](https://github.com/developmentseed/lonboard/pull/1283)

## Docs updates

* Show how to change the output of `viz` by @kylebarron in https://github.com/developmentseed/lonboard/pull/1297
* Add SedonaDB to the ecosystem docs by @kylebarron in https://github.com/developmentseed/lonboard/pull/1299
* Fix the examples on the Shiny, GeoPandas and GeoArrow pages by @kylebarron in https://github.com/developmentseed/lonboard/pull/1296

## New examples

* Add an example for Geohash Layer by @aryanxk02 in https://github.com/developmentseed/lonboard/pull/1242

## All updates

Refer to the [changelog] for all updates.

[changelog]: ../../CHANGELOG.md/#0170-2026-10-02

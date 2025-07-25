# Changelog

## [0.11.1] - 2025-06-18

### Bug fixes :bug:

- fix: move duckdb imports to inside function by @danielsparing in https://github.com/developmentseed/lonboard/pull/813
- chore: Use `>=` in typing-extensions version constraint by @kylebarron in https://github.com/developmentseed/lonboard/pull/814

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.11.0...v0.11.1

## [0.11.0] - 2025-06-17

### Breaking changes :hammer:

- Require Python 3.9 or higher by @kylebarron in https://github.com/developmentseed/lonboard/pull/743

### New features :sparkles:

- feat: Reinstate tooltip by @vgeorge in https://github.com/developmentseed/lonboard/pull/736.
  You can now turn on the tooltip by passing `show_tooltip=True` to `Map`. You may also want to pass `show_side_panel=False` to disable the side panel.
- Clicked point to Lonboard map by @ATL2001 in https://github.com/developmentseed/lonboard/pull/671
- feat: Support `geoarrow.box` arrays from GeoArrow 0.2 spec by @kylebarron in https://github.com/developmentseed/lonboard/pull/793
- feat: Allow passing Arrow table as positional argument to layer constructors by @kylebarron in https://github.com/developmentseed/lonboard/pull/795
- Switch to the DuckDB Expression API to mitigate sql injection risk by @danielsparing in https://github.com/developmentseed/lonboard/pull/777

### Visual changes :art:

- Improve side panel layout by @vgeorge in https://github.com/developmentseed/lonboard/pull/701

### Bug fixes :bug:

- Scope tailwind preflight styles by @Bjoern-Rapp in https://github.com/developmentseed/lonboard/pull/740
- Pass state in `to_html` by @kylebarron in https://github.com/developmentseed/lonboard/pull/726
- use dependency state in export by @knaaptime in https://github.com/developmentseed/lonboard/pull/731
- fix: ensure GeoArrow field names are set in conversion from shapely by @kylebarron in https://github.com/developmentseed/lonboard/pull/794
- Fix accessing default connection for duckdb 1.2 by @kylebarron in https://github.com/developmentseed/lonboard/pull/772
- Sanitize geomcolname by @danielsparing in https://github.com/developmentseed/lonboard/pull/769

### Documentation :book:

- Replace DS Medium link by LinkedIn by @willemarcel in https://github.com/developmentseed/lonboard/pull/700
- Geoarrow docstring update by @ATL2001 in https://github.com/developmentseed/lonboard/pull/705
- Add docs page with external resources by @kylebarron in https://github.com/developmentseed/lonboard/pull/710
- Panel example update by @ATL2001 in https://github.com/developmentseed/lonboard/pull/746
- docs: Reword section in "How it works" to reflect GeoParquet 1.1 by @kylebarron in https://github.com/developmentseed/lonboard/pull/804
- docs: Add duckdb intersphinx mapping by @kylebarron in https://github.com/developmentseed/lonboard/pull/800
- Remove references to custom connection parameter by @danielsparing in https://github.com/developmentseed/lonboard/pull/784
- updates for polygon layer documentation by @ATL2001 in https://github.com/developmentseed/lonboard/pull/789

### Internal changes :wrench:

- Switch dependency management to uv by @kylebarron in https://github.com/developmentseed/lonboard/pull/721
- Support Py3.12 in tests by constraining pyproj in lockfile to versions with wheels by @ceholden in https://github.com/developmentseed/lonboard/pull/745
- Enable more ruff linters by @kylebarron in https://github.com/developmentseed/lonboard/pull/753
- Reduce ruff warnings by @danielsparing in https://github.com/developmentseed/lonboard/pull/778
- chore: Ensure support for GeoArrow 0.2 CRS by @kylebarron in https://github.com/developmentseed/lonboard/pull/797
- chore: Bump deck.gl to 9.1 by @kylebarron in https://github.com/developmentseed/lonboard/pull/802
- test: Test that parsing WKB/WKT works with Arrow view types by @kylebarron in https://github.com/developmentseed/lonboard/pull/801

### New Contributors

- @knaaptime made their first contribution in https://github.com/developmentseed/lonboard/pull/731
- @ceholden made their first contribution in https://github.com/developmentseed/lonboard/pull/745
- @Bjoern-Rapp made their first contribution in https://github.com/developmentseed/lonboard/pull/740
- @danielsparing made their first contribution in https://github.com/developmentseed/lonboard/pull/769

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.10.3...v0.11.0

## [0.10.3] - 2024-10-15

### Fixes :bug:

- Downgrade minimum traitlets version to fix use with Colab. https://github.com/developmentseed/lonboard/pull/687

## [0.10.2] - 2024-10-10

### Fixes :bug:

- Fix using `TripsLayer.from_movingpandas` with numpy v2.

## [0.10.1] - 2024-10-08

### Fixes :bug:

- Fix import when pandas not installed.

## [0.10.0] - 2024-10-07

### New! :sparkles:

- **New `TripsLayer`** for animating moving objects, which integrates with [MovingPandas](https://github.com/movingpandas/movingpandas). See the [Air Traffic Control example](https://developmentseed.org/lonboard/latest/examples/air-traffic-control/) and the [MovingPandas integration example](https://developmentseed.org/lonboard/latest/examples/ais-movingpandas/).
- **New [`ColumnLayer`](https://developmentseed.org/lonboard/latest/api/layers/column-layer/)** for rendering extruded cylinders. See the [new `ColumnLayer` example](https://developmentseed.org/lonboard/latest/examples/column-layer/).
- **Removed required dependencies!** `geopandas`, `pandas`, `shapely`, `pyarrow`, `matplotlib`, and `palettable` are now _optional_ dependencies. Lonboard will still work out of the box with them, but they aren't required to use Lonboard. This gives Lonboard a smaller footprint and makes it easier to use in environments such as [Pyodide](https://pyodide.org/).
- You can now **draw bounding boxes on the map**. This is exposed as the `selected_bounds` attribute on the `Map` object, stored as a two-dimensional bounding box `(minx, miny, maxx, maxy)`.
- **Improved documentation**
  - [How to use Lonboard in pyodide](https://developmentseed.org/lonboard/latest/ecosystem/pyodide/), a Python environment that is fully running in your browser.
  - Add linked maps example by @ATL2001 in https://github.com/developmentseed/lonboard/pull/655
  - Add troubleshooting doc by @kylebarron in https://github.com/developmentseed/lonboard/pull/654
  - Add longraph to showcase by @kylebarron in https://github.com/developmentseed/lonboard/pull/595
- **New `Map.add_layer` method** for easily adding more layer(s) to an existing `Map` instance.
- Add `highlight_color` to change the color of `auto_highlight` by @kylebarron in https://github.com/developmentseed/lonboard/pull/666
- Use deterministic colors in `viz` by @kylebarron in https://github.com/developmentseed/lonboard/pull/621
- Categorical data filtering. The `DataFilterExtension` now has a [`filter_categories` attribute](https://developmentseed.org/lonboard/latest/api/layer-extensions/data-filter-extension/#lonboard.layer_extension.DataFilterExtension--filter_categories) that lets you filter categorical data on the map. by @kylebarron in https://github.com/developmentseed/lonboard/pull/609

### Breaking Changes :hammer:

- The tooltip shown on hover was **replaced with a side panel**. You now must **click** on a geometry to view its attributes. By @vgeorge in https://github.com/developmentseed/lonboard/pull/636

### Fixes :bug:

- We've switched from storing `list` objects to storing `tuple` objects (e.g. the list of layers in a `Map`). The immutability of the `tuple` ensures that a any changes in the sequence of layers will be propagated to the frontend.Fixed in https://github.com/developmentseed/lonboard/pull/620
- A class of bugs was fixed when using Arrow input, where the chunking structure of the main `table` did not match the chunking of accessors. Fixed in https://github.com/developmentseed/lonboard/pull/644
- Fix reading from DuckDB with only geometry column by @kylebarron in https://github.com/developmentseed/lonboard/pull/625
- Fix attribution by @vgeorge in https://github.com/developmentseed/lonboard/pull/561

### New Contributors

- @MarcSkovMadsen made their first contribution in https://github.com/developmentseed/lonboard/pull/539
- @ATL2001 made their first contribution in https://github.com/developmentseed/lonboard/pull/655

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.9.3...v0.10.0

## [0.9.3] - 2024-05-27

### Fixes :bug:

- Fix reprojecting GeoArrow input by @kylebarron in https://github.com/developmentseed/lonboard/pull/532

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.9.2...v0.9.3

## [0.9.2] - 2024-05-14

### Fixes :bug:

- Reverse the layer order for automatically split geometry by @RaczeQ in https://github.com/developmentseed/lonboard/pull/516

### What's Changed

- Perf: Use ravel, not flatten, for numpy to pyarrow by @kylebarron in https://github.com/developmentseed/lonboard/pull/512
- Update docstring in as_html by @kylebarron in https://github.com/developmentseed/lonboard/pull/519
- Add type checks to fly_to by @kylebarron in https://github.com/developmentseed/lonboard/pull/521
- Add pypi classifiers by @kylebarron in https://github.com/developmentseed/lonboard/pull/523

### New Contributors

- @RaczeQ made their first contribution in https://github.com/developmentseed/lonboard/pull/516

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.9.1...v0.9.2

## [0.9.1] - 2024-05-07

### Fixes :bug:

- Fix parquet-wasm WASM version mismatch by @kylebarron in https://github.com/developmentseed/lonboard/pull/508

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.9.0...v0.9.1

## [0.9.0] - 2024-05-06

### New! :sparkles:

- Direct [DuckDB Spatial](https://duckdb.org/docs/extensions/spatial.html) integration. Refer to the [DuckDB example notebook](https://developmentseed.org/lonboard/latest/examples/duckdb/) and the [DuckDB page](https://developmentseed.org/lonboard/latest/ecosystem/duckdb/) in the documentation. by @kylebarron in https://github.com/developmentseed/lonboard/pull/498
- Add [overture buildings notebook](https://developmentseed.org/lonboard/latest/examples/overture-maps/) by @kylebarron in https://github.com/developmentseed/lonboard/pull/479
- Adding [PathStyleExtension](https://developmentseed.org/lonboard/latest/api/layer-extensions/path-style-extension/) code by @shriv in https://github.com/developmentseed/lonboard/pull/487
- Handle mixed geometry types in `viz` by @kylebarron in https://github.com/developmentseed/lonboard/pull/495
- Render map as static HTML file by @kylebarron in https://github.com/developmentseed/lonboard/pull/474. You can use `Map.as_html` to render a map in notebook environments that support HTML but not widgets.
- Improved integration with [geoarrow-pyarrow](https://geoarrow.org/geoarrow-python/main/pyarrow.html) by @kylebarron in https://github.com/developmentseed/lonboard/pull/470

### Fixes :bug:

- Updated Map keyword arguments by @kylebarron in https://github.com/developmentseed/lonboard/pull/496
- validate basemap style is a url by @kylebarron in https://github.com/developmentseed/lonboard/pull/497

### New Contributors

- @willemarcel made their first contribution in https://github.com/developmentseed/lonboard/pull/486
- @shriv made their first contribution in https://github.com/developmentseed/lonboard/pull/487

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.8.0...v0.9.0

## [0.8.0] - 2024-04-05

### New! :sparkles:

- A new [`PolygonLayer`](https://developmentseed.org/lonboard/v0.8.0/api/layers/polygon-layer/)! This layer renders polygon outlines for easier visibility. @kylebarron in https://github.com/developmentseed/lonboard/pull/330
- An example using `PolygonLayer` by @naomatheus in https://github.com/developmentseed/lonboard/pull/351
- Sync view state between JS and Python by @kylebarron in https://github.com/developmentseed/lonboard/pull/448
- Support geoarrow array input into `viz()` by @kylebarron in https://github.com/developmentseed/lonboard/pull/427
- Internal architecture documentation by @kylebarron in https://github.com/developmentseed/lonboard/pull/450

### Fixes :bug:

- Fix CLI with unset `geometry_name` by @kylebarron in https://github.com/developmentseed/lonboard/pull/451

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.7.1...v0.8.0

## [0.7.1] - 2024-03-22

### Fixes :bug:

- Fix CLI with geopackage files by @kylebarron in https://github.com/developmentseed/lonboard/pull/434

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.7.0...v0.7.1

## [0.7.0] - 2024-03-21

### New! :sparkles:

- There's a [new command-line interface (CLI)](https://developmentseed.org/lonboard/v0.7.0/cli)! Use the `lonboard` command to quickly visualize one or more data files readable by GDAL! For example: `lonboard admins.geojson features.gpkg`. By @kylebarron in https://github.com/developmentseed/lonboard/pull/379
- Type hinting for constructors and `from_geopandas` method. This should make it easier to pass the correct parameters into layers. This has been tested to work in IDEs like VSCode, but unfortunately appears not to work in JupyterLab. By @kylebarron in https://github.com/developmentseed/lonboard/pull/399

  ![Type hints are now supported in constructors.](assets/type-hints-constructor.jpg)

- Warn on missing CRS. One of the most common reasons that you might see an empty map is from accidentally visualizing data that is not in EPSG 4326 (longitude-latitude). We now emit a warning for data that doesn't have a CRS defined on the data. By @kylebarron in https://github.com/developmentseed/lonboard/pull/395.
- Lonboard is [now on `conda-forge`](https://prefix.dev/channels/conda-forge/packages/lonboard)! Install with `conda install -c conda-forge lonboard`. By @giswqs in https://github.com/developmentseed/lonboard/pull/223
- Add [PointCloudLayer](https://developmentseed.org/lonboard/v0.7.0/api/layers/point-cloud-layer/). By @kylebarron in https://github.com/developmentseed/lonboard/pull/396
- Add [fly-to map action](https://developmentseed.org/lonboard/v0.7.0/api/map/#lonboard.Map.fly_to) to "fly" the map to a new location. By @kylebarron in https://github.com/developmentseed/lonboard/pull/408
- [Docs showcase page](https://developmentseed.org/lonboard/v0.7.0/examples/) by @kylebarron in https://github.com/developmentseed/lonboard/pull/401
- Improve default colors in [`viz`](https://developmentseed.org/lonboard/v0.7.0/api/viz/). We now attempt to apply some basic styling onto data passed into `viz`. This will likely further improve in the future. By @kylebarron in https://github.com/developmentseed/lonboard/pull/389

### Fixes :bug:

- Set exported HTML height to 100% by @kylebarron in https://github.com/developmentseed/lonboard/pull/377
- Raise error on single input to MultiRangeSlider by @kylebarron in https://github.com/developmentseed/lonboard/pull/367
- Fix pandas `to_numeric` FutureWarning by @kylebarron in https://github.com/developmentseed/lonboard/pull/368
- Fix viewing polygons in local html files by @kylebarron in https://github.com/developmentseed/lonboard/pull/387
- Fix: fix sliced array input for reprojection by @kylebarron in https://github.com/developmentseed/lonboard/pull/391
- Fix: Don't reproject for epsg:4326 input by @kylebarron in https://github.com/developmentseed/lonboard/pull/392
- Fix: Fix weighted centroid calculation by @kylebarron in https://github.com/developmentseed/lonboard/pull/393
- Fix `viz()` with `__geo_interface__` input by @kylebarron in https://github.com/developmentseed/lonboard/pull/426
- Add DataFilterExtension notebook to website by @kylebarron in https://github.com/developmentseed/lonboard/pull/362
- Allow non-compliant geoarrow CRS metadata by @kylebarron in https://github.com/developmentseed/lonboard/pull/369
- Automatically parse geoarrow.wkb to native geoarrow by @kylebarron in https://github.com/developmentseed/lonboard/pull/372
- Parse GeoParquet metadata by @kylebarron in https://github.com/developmentseed/lonboard/pull/407
- CLI: 'crs' in geoparquet metadata should be optional. by @jwass in https://github.com/developmentseed/lonboard/pull/411

### Other changes

- Creating a new user bug report by @emmalu in https://github.com/developmentseed/lonboard/pull/386
- Update epic template by @emmalu in https://github.com/developmentseed/lonboard/pull/382
- NormalAccessor by @naomatheus in https://github.com/developmentseed/lonboard/pull/376
- Conda: Try including `manifest.in` file for `static` folder inclusion by @kylebarron in https://github.com/developmentseed/lonboard/pull/421
- Switch to animated hero image by @kylebarron in https://github.com/developmentseed/lonboard/pull/423
- Add CRS to GeoDataFrame in notebook examples by @kylebarron in https://github.com/developmentseed/lonboard/pull/419

## New Contributors

- @emmalu made their first contribution in https://github.com/developmentseed/lonboard/pull/382
- @naomatheus made their first contribution in https://github.com/developmentseed/lonboard/pull/376
- @jwass made their first contribution in https://github.com/developmentseed/lonboard/pull/411
- @giswqs made their first contribution in https://github.com/developmentseed/lonboard/pull/223

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.6.0...v0.7.0

## [0.6.0] - 2024-02-13

### New! :sparkles:

- DataFilterExtension by @kylebarron in https://github.com/developmentseed/lonboard/pull/278
- Multi-range sliders for DataFilterExtension by @kylebarron in https://github.com/developmentseed/lonboard/pull/340
- BitmapLayer and BitmapTileLayer by @kylebarron in https://github.com/developmentseed/lonboard/pull/288
- Improved GeoArrow interop by @kylebarron in https://github.com/developmentseed/lonboard/pull/308
- Allow passing a positional `layers` object into `Map` by @kylebarron in https://github.com/developmentseed/lonboard/pull/319
- GeoArrow-based multithreaded coordinate reprojection by @kylebarron in https://github.com/developmentseed/lonboard/pull/337
- Support `pyarrow.Table` with `geoarrow.pyarrow` extension types as geometry columns by @jorisvandenbossche in https://github.com/developmentseed/lonboard/pull/218
- Add ecosystem/integrations documentation by @kylebarron in https://github.com/developmentseed/lonboard/pull/350

### Fixes :bug:

- Add font to index.css to fix static HTML export by @jtmiclat in https://github.com/developmentseed/lonboard/pull/284
- Fix displaying tooltip for first row by @kylebarron in https://github.com/developmentseed/lonboard/pull/287
- accept matplotlib colormap input to apply_cmap by @kylebarron in https://github.com/developmentseed/lonboard/pull/289
- Use preferred OSM tile url by @kylebarron in https://github.com/developmentseed/lonboard/pull/290
- set max zoom on osm layer by @kylebarron in https://github.com/developmentseed/lonboard/pull/291
- Update contributor docs by @kylebarron in https://github.com/developmentseed/lonboard/pull/316
- Check epsg:4326 bounds in layer creation by @kylebarron in https://github.com/developmentseed/lonboard/pull/317
- add reference for installing from source by @kylebarron in https://github.com/developmentseed/lonboard/pull/318
- Fix inferring number of rows per chunk by @kylebarron in https://github.com/developmentseed/lonboard/pull/327
- Fix null checks by @kylebarron in https://github.com/developmentseed/lonboard/pull/331
- Set max number of chunks per layer by @kylebarron in https://github.com/developmentseed/lonboard/pull/332
- Move accessor length validation to serialization by @kylebarron in https://github.com/developmentseed/lonboard/pull/333
- Deduplicate serialization for accessors by @kylebarron in https://github.com/developmentseed/lonboard/pull/334
- Multi-dimensional GPU-based data filtering by @kylebarron in https://github.com/developmentseed/lonboard/pull/335
- Bump anywidget to 0.9 & simplify Wasm initialization by @kylebarron in https://github.com/developmentseed/lonboard/pull/344
- Fix null checks by @kylebarron in https://github.com/developmentseed/lonboard/pull/348
- docs fixes by @kylebarron in https://github.com/developmentseed/lonboard/pull/354
- Add `DataFilterExtension` example by @kylebarron in https://github.com/developmentseed/lonboard/pull/358
- fix arc layer default arguments by @kylebarron in https://github.com/developmentseed/lonboard/pull/359

## New Contributors

- @jtmiclat made their first contribution in https://github.com/developmentseed/lonboard/pull/284
- @jorisvandenbossche made their first contribution in https://github.com/developmentseed/lonboard/pull/218

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.5.0...v0.6.0

## [0.5.0] - 2023-12-01

### New Features

- Improve map height by @vgeorge in https://github.com/developmentseed/lonboard/pull/220
- Add method to apply a categorical colormap by @kylebarron in https://github.com/developmentseed/lonboard/pull/251
- Deduce environment and set map height in colab and vscode by @kylebarron in https://github.com/developmentseed/lonboard/pull/252
- Add various carto basemaps as options by @kylebarron in https://github.com/developmentseed/lonboard/pull/268
- Sync the clicked index back to Python by @kylebarron in https://github.com/developmentseed/lonboard/pull/270
- Set `width_min_pixels` in PathLayer example by @kylebarron in https://github.com/developmentseed/lonboard/pull/276
- Bump deck.gl layers for performance benefits by @kylebarron in https://github.com/developmentseed/lonboard/pull/277

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.4.2...v0.5.0

## [0.4.2] - 2023-11-13

### Fixed

- Fixed ScatterplotLayer rendering by @kylebarron in https://github.com/developmentseed/lonboard/pull/246

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.4.1...v0.4.2

## [0.4.1] - 2023-11-13

### Fixed

- Fixed Polygon rendering by @kylebarron in https://github.com/developmentseed/lonboard/pull/243

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.4.0...v0.4.1

## [0.4.0] - 2023-11-10

### New Features

- New `HeatmapLayer`
- New `experimental` module, with new layers (`ArcLayer`, `TextLayer`) and "layer extensions" (`BrushingExtension`, `CollisionFilterExtension`).
- New "migration" notebook using the experimental `ArcLayer`.

### Fixed

- Add pandas v2 requirement by @kylebarron in https://github.com/developmentseed/lonboard/pull/229
- bump anywidget to 0.7.1 by @kylebarron in https://github.com/developmentseed/lonboard/pull/233

  This should error when the JS files have not been included when packaging.

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.3.0...v0.4.0

## [0.3.0] - 2023-11-07

### New Features

- Save widget to standalone HTML file by @kylebarron in https://github.com/developmentseed/lonboard/pull/199
- Support for rendering inside Visual Studio Code
- Allow customized picking radius by @kylebarron in https://github.com/developmentseed/lonboard/pull/212
- New example notebooks
- Automatically downcast data types in `from_geopandas` by @kylebarron in https://github.com/developmentseed/lonboard/pull/195

### Fixed

- Allow pandas series as accessor to FloatAccessor by @kylebarron in https://github.com/developmentseed/lonboard/pull/208
- Raise error when creating class with unknown keyword argument by @kylebarron in https://github.com/developmentseed/lonboard/pull/209
- fix tooltip rendering when not hovering over an object by @kylebarron in https://github.com/developmentseed/lonboard/pull/215

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.2.0...v0.3.0

## [0.2.0] - 2023-11-01

### Breaking Changes

- Layers no longer render a map object. Instead, pass one or more layer instances into a `lonboard.Map` and display that.

### New Features

- Support multiple layers on a single map.
- Tooltip with data information on hover.
- Allow hex string color input to ColorAccessor.
- Versioned documentation website
- New examples
- Experimental API to change map height

### Fixed

- Fix handling of 3d coordinates by @kylebarron in https://github.com/developmentseed/lonboard/pull/160
- Improved validation error messages by @kylebarron in https://github.com/developmentseed/lonboard/pull/161

### New Contributors

- @chrisgervang made their first contribution in https://github.com/developmentseed/lonboard/pull/150

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.1.2...v0.2.0

## [0.1.2] - 2023-10-24

- _Actually_ update `@geoarrow/deck.gl-layers` to version 0.2.0, whoops 😅

## [0.1.1] - 2023-10-23

- Updates to `@geoarrow/deck.gl-layers` version 0.2.0:
  - Fixed MultiPolygon rendering
  - Fixed rendering of polygons with holes.
  - Polygon rendering is roughly 35% faster.

## [0.1.0] - 2023-10-17

- Initial public release.
- Initial support for `ScatterplotLayer`, `PathLayer`, and `SolidPolygonLayer`.

# Changelog

## [0.6.0] - 2024-02-13

### New! :sparkles:

* DataFilterExtension by @kylebarron in https://github.com/developmentseed/lonboard/pull/278
* Multi-range sliders for DataFilterExtension by @kylebarron in https://github.com/developmentseed/lonboard/pull/340
* BitmapLayer and BitmapTileLayer by @kylebarron in https://github.com/developmentseed/lonboard/pull/288
* Improved GeoArrow interop by @kylebarron in https://github.com/developmentseed/lonboard/pull/308
* Allow passing a positional `layers` object into `Map` by @kylebarron in https://github.com/developmentseed/lonboard/pull/319
* GeoArrow-based multithreaded coordinate reprojection by @kylebarron in https://github.com/developmentseed/lonboard/pull/337
* Support `pyarrow.Table` with `geoarrow.pyarrow` extension types as geometry columns by @jorisvandenbossche in https://github.com/developmentseed/lonboard/pull/218
* Add ecosystem/integrations documentation by @kylebarron in https://github.com/developmentseed/lonboard/pull/350

### Fixes :bug:

* Add font to index.css to fix static HTML export by @jtmiclat in https://github.com/developmentseed/lonboard/pull/284
* Fix displaying tooltip for first row by @kylebarron in https://github.com/developmentseed/lonboard/pull/287
* accept matplotlib colormap input to apply_cmap by @kylebarron in https://github.com/developmentseed/lonboard/pull/289
* Use preferred OSM tile url by @kylebarron in https://github.com/developmentseed/lonboard/pull/290
* set max zoom on osm layer by @kylebarron in https://github.com/developmentseed/lonboard/pull/291
* Update contributor docs by @kylebarron in https://github.com/developmentseed/lonboard/pull/316
* Check epsg:4326 bounds in layer creation by @kylebarron in https://github.com/developmentseed/lonboard/pull/317
* add reference for installing from source by @kylebarron in https://github.com/developmentseed/lonboard/pull/318
* Fix inferring number of rows per chunk by @kylebarron in https://github.com/developmentseed/lonboard/pull/327
* Fix null checks by @kylebarron in https://github.com/developmentseed/lonboard/pull/331
* Set max number of chunks per layer by @kylebarron in https://github.com/developmentseed/lonboard/pull/332
* Move accessor length validation to serialization by @kylebarron in https://github.com/developmentseed/lonboard/pull/333
* Deduplicate serialization for accessors by @kylebarron in https://github.com/developmentseed/lonboard/pull/334
* Multi-dimensional GPU-based data filtering by @kylebarron in https://github.com/developmentseed/lonboard/pull/335
* Bump anywidget to 0.9 & simplify Wasm initialization by @kylebarron in https://github.com/developmentseed/lonboard/pull/344
* Fix null checks by @kylebarron in https://github.com/developmentseed/lonboard/pull/348
* docs fixes by @kylebarron in https://github.com/developmentseed/lonboard/pull/354
* Add `DataFilterExtension` example by @kylebarron in https://github.com/developmentseed/lonboard/pull/358
* fix arc layer default arguments by @kylebarron in https://github.com/developmentseed/lonboard/pull/359

## New Contributors

* @jtmiclat made their first contribution in https://github.com/developmentseed/lonboard/pull/284
* @jorisvandenbossche made their first contribution in https://github.com/developmentseed/lonboard/pull/218

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

# Migrate `RasterModel` TMS path to `RasterTileLayer`

## Goal

Simplify [src/model/layer/raster.ts](../../../src/model/layer/raster.ts) by
replacing its hand-wired `TileLayer` + `RasterTileset2D` + per-tile `RasterLayer`
plumbing with the single composite `RasterTileLayer` that
`@developmentseed/deck.gl-raster@^0.6.0-beta.1` now exports.

This is a prototype: validate that `RasterTileLayer` is a drop-in replacement
for the current TMS code path, with no user-facing API or behavior change.

## Scope

- **In scope:** the TMS path (`renderTileMatrixSet`) in
  [src/model/layer/raster.ts](../../../src/model/layer/raster.ts).
- **Out of scope:**
  - The non-TMS fallback in `render()` (the `TileLayer` + `BitmapLayer` Web
    Mercator path stays unchanged).
  - The Python widget side ([lonboard/layer/_raster.py](../../../lonboard/layer/_raster.py))
    — the `raster-get-tile-data` message protocol does not change.
  - Any user-facing trait, method, or constructor signature on
    `lonboard.RasterLayer`.

## Current state

`renderTileMatrixSet` builds three things by hand:

1. A `TileMatrixSetAdaptor` and a `RasterTileset2DFactory` subclass that
   captures the descriptor in its constructor.
2. A `TileLayer` whose `getTileData` fetches encoded bytes from Python via
   `invoke()`, decodes to an `ImageBitmap`, and computes per-tile forward /
   inverse affine transforms by calling `morecantile.tileTransform` and
   `@developmentseed/affine`'s `invert`/`apply`. Returns
   `{ image, forwardTransform, inverseTransform }`.
3. A `renderSubLayers` (`renderRasterSubLayer`) that constructs the inner
   `RasterLayer` from `@developmentseed/deck.gl-raster` and threads a full
   `ReprojectionFns` object through it (the per-tile transforms plus
   `proj4`-derived converters between source CRS ↔ EPSG:4326).

## Target state

`renderTileMatrixSet` constructs one `RasterTileLayer` directly:

```ts
return new RasterTileLayer<TileData>({
  ...this.baseLayerProps(),
  ...this.layerProps(),
  tilesetDescriptor,
  getTileData: this.getTileData,
  renderTile: (data) => ({ image: data.image }),
});
```

Where:

- `tilesetDescriptor` is a `TileMatrixSetAdaptor` constructed with all four
  projection functions required by the 0.6 API:
  `projectTo4326`, `projectFrom4326`, `projectTo3857`, `projectFrom3857`. The
  existing `proj4.Converter` instances on `this.converters` already supply
  both directions; expose `.forward()` and `.inverse()` for each.
- `TileData` is `MinimalTileData & { image: TextureSource }` — i.e.
  `{ image, width, height }`. No `forwardTransform`/`inverseTransform` fields;
  the per-tile transform is now resolved internally by `RasterTileLayer` via
  `tilesetDescriptor.levels[z].tileTransform(col, row)`.
- `getTileData(tile, options)` continues to call `invoke()` to fetch encoded
  bytes from Python, decodes to `ImageBitmap`, and returns
  `{ image, width: image.width, height: image.height }`. The abort signal
  comes from `options.signal` (the composed layer + per-tile signal) rather
  than `tile.signal`.
- `renderTile(data)` is a one-liner that returns `{ image: data.image }`.

## Code that gets removed

From [src/model/layer/raster.ts](../../../src/model/layer/raster.ts):

- Imports: `RasterLayer` and `RasterTileset2D` from
  `@developmentseed/deck.gl-raster`; `tileTransform` from
  `@developmentseed/morecantile`; `apply` and `invert` from
  `@developmentseed/affine`; `ReprojectionFns` from
  `@developmentseed/raster-reproject`.
- The `RasterTileset2DFactory` subclass inside `renderTileMatrixSet`.
- The `renderRasterSubLayer` method.
- The `forwardTransform` / `inverseTransform` fields on `TileData`.

New imports: `RasterTileLayer` from `@developmentseed/deck.gl-raster`.

## Code that stays

- The non-TMS path in `render()` — the `TileLayer` + `BitmapLayer` Web Mercator
  fallback is untouched.
- All `BaseLayerModel` plumbing and the synced trait fields (`tileSize`,
  `zoomOffset`, `maxZoom`, `minZoom`, `extent`, `maxCacheSize`,
  `debounceTime`).
- The `accessConverters` helper (still used by the fallback path; harmless to
  keep).
- The `dataViewToImageBitmap` decoder.
- The `MSG_KIND` constant and the `TileResponse` shape.

## Type compatibility

`RasterTileLayerProps` extends `CompositeLayerProps` and re-picks a subset of
`TileLayerProps` (`tileSize`, `zoomOffset`, `maxZoom`, `minZoom`, `extent`,
`debounceTime`, `maxCacheSize`, `maxCacheByteSize`, `maxRequests`,
`refinementStrategy`). The current `layerProps()` emits only fields in that
subset, and `baseLayerProps()` emits standard `Layer` props (`pickable`,
`opacity`, `visible`, …) that are valid on `CompositeLayerProps`. Spreading
both is type-safe.

## Verification

1. `npm run build` and `npm run check` succeed with no new errors.
2. Manually load a PMTiles raster via `RasterLayer.from_pmtiles` and a COG via
   `RasterLayer.from_geotiff` (existing notebooks like `raster.ipynb` and
   `raster-pmtiles.ipynb`) and confirm tiles render with the same visual
   result as before the migration.
3. The Web Mercator (no-TMS) fallback continues to work — quick smoke test
   with a layer constructed without a `_tile_matrix_set`.

## Risks

- The 0.6 `TileMatrixSetAdaptor` constructor signature now requires
  `projectFrom4326` and `projectFrom3857` in addition to the forward
  directions. Easy to satisfy from the existing `proj4` converters.
- `RasterTileLayer` may surface different default values for shared props
  (`tileSize`, `maxError`, etc.) than the manually-built `TileLayer` did.
  Address by inspecting visible behavior on the verification step and, if
  needed, passing the previous values explicitly.

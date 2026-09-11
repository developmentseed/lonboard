# Lonboard Zarr Support (v1 Prototype)

## Goal

Add Zarr visualization support to Lonboard's `RasterLayer` in the same "Python
fetches and renders, JS displays" style as the existing GeoTIFF support. Users
can point Lonboard at a Zarr store (either directly via `zarr-python` or via
`xarray` on top of a Zarr backend) and get the same tiled, reprojected,
on-demand rendering experience as `RasterLayer.from_geotiff`.

v1 is scoped narrowly: **Python fetches chunks asynchronously; a user-provided
`render_tile` callback encodes each tile as a PNG/JPEG/WebP; the browser
decodes and displays.** No WebGL-side rendering, no non-spatial-dim animation.
Those are deferred to future work.

## Motivation

Two user populations want Zarr in Lonboard today:

- Earth-science / climate users (Pangeo ecosystem) who already use `xarray` on
  top of Zarr stores. They expect the xarray API for labeled selection.
- Users who want low-overhead direct access to `zarr-python` (e.g. large
  analytical workflows where xarray's overhead matters, or users already
  familiar with the Zarr data model).

The JS side of `@developmentseed/deck.gl-raster` has a working `ZarrLayer`
that fetches and renders Zarr chunks entirely in the browser (see
`examples/dynamical-zarr-ecmwf`). That layer is **not** what this spec
delivers — Lonboard deliberately routes Zarr fetching through Python, for the
same reasons documented in Lonboard's initial-COG blog post:

- Users often have private / authenticated data that Python can access but
  the browser cannot; credentials don't serialize cleanly.
- Users want to customize rendering with arbitrary Python code (NumPy, PIL,
  matplotlib colormaps, Python ML models, …) without writing JavaScript.
- Lonboard's core value prop: *"if you can load it in Python, you can
  visualize it in Lonboard."*

## Scope

### In scope (v1)

- `RasterLayer.from_zarr(arr, selection=..., metadata=..., render_tile=...)`
  accepting an opened `zarr.AsyncArray` or `zarr.Array`.
- `RasterLayer.from_xarray(da, render_tile=...)` accepting a
  pre-selected `xarray.DataArray`.
- Async per-tile fetching through the opened source, with deck.gl's
  `maxRequests` as the concurrency limiter (no Python-side semaphore).
- JS-side refactor of `RasterModel` to accept a generic `TilesetDescriptor`
  from Python instead of being hardcoded to `TileMatrixSet`. `TileMatrixSet`
  becomes one of the descriptor shapes that Python can send.
- CRS + affine discovery for `from_xarray` via a defined priority order
  (see [CRS & affine discovery](#crs--affine-discovery-for-from_xarray)),
  with an explicit override escape hatch.
- Documentation (notebook example using a public Zarr store; tutorial in
  the mkdocs site).

### Out of scope (v1)

- WebGL-side rendering of Zarr data. Users pass PNGs/JPEGs/WebP from Python;
  the browser only decodes and displays. Future work after Python → WebGL
  DSL transpilation lands.
- **Interactive** animation over non-spatial dimensions. The `selection`
  is fixed at layer construction; Lonboard does not expose a way to scrub
  or play through a non-spatial axis yet. The *shape* of the selection is
  unrestricted — a user may pin every non-spatial dim to a scalar, keep a
  dim (`None`), or pass a Python `slice` — but whatever shape they choose,
  every tile fetch returns the same-shape ND array, and `render_tile` is
  responsible for reducing it to 2D (e.g. averaging a time dim, summing
  over bands).
- `RasterTileLayer` refactor in `@developmentseed/deck.gl-raster`. That
  refactor is attractive but orthogonal; it can happen before or after this
  work without affecting the API shape. Tracked separately.
- Python-side concurrency limiting. deck.gl's `TileLayer.maxRequests`
  already caps fan-out; revisit if we observe overload.
- Client-side Zarr fetching from the browser (the existing deck.gl-zarr
  path). Not ruled out for a later version, but orthogonal.

## Architecture

### Current state

Lonboard's raster pipeline (as of commit `e85d119`) is:

- Python: `RasterLayer.from_geotiff(geotiff, render_tile=...)` holds the
  `async_geotiff.GeoTIFF` instance and the user's `render_tile` callback.
  The widget serializes a `TileMatrixSet` (`_tile_matrix_set`) and a
  PROJJSON CRS (`_crs`) to JS.
- JS: [`src/model/layer/raster.ts`](../../../src/model/layer/raster.ts)
  reconstructs a `TileMatrixSetTileset` from the TMS, and creates a
  `TileLayer` whose `getTileData` round-trips each tile to Python via the
  anywidget Jupyter comm (`MSG_KIND = "raster-get-tile-data"`).
- Per-tile: Python calls `geotiff.fetch_tile(x, y, z)`, passes the result
  through the user's `render_tile`, and returns encoded image bytes. JS
  decodes to an `ImageBitmap` and feeds deck.gl-raster's `RasterLayer` with
  `reprojectionFns` built from per-tile affines.

The JS side is **hardcoded to `TileMatrixSet`**. Zarr does not use TMS —
Zarr multiscales are affine-based and allow arbitrary chunk layouts. This
is the core JS-side change needed.

### Target state

#### Python side — `TileSource` abstraction

A single internal protocol describes any tiled raster data source:

```python
class TileSource(Protocol):
    tileset_descriptor: TilesetDescriptor  # serialized to JS at __init__
    source_crs: CRS                        # pyproj CRS; serialized as PROJJSON

    async def fetch_tile(
        self,
        x: int,
        y: int,
        z: int,
        *,
        signal: AbortSignal | None = None,
    ) -> TileData | None: ...
```

Three implementations:

- `GeoTiffTileSource` — wraps `async_geotiff.GeoTIFF`; derives descriptor
  from GeoTIFF overviews (existing behavior, refactored onto the protocol).
- `ZarrTileSource` — wraps `zarr.AsyncArray` + `selection` dict + metadata;
  derives descriptor from GeoZarr multiscales (or a single-resolution
  descriptor if multiscales absent).
- `XarrayTileSource` — wraps `xarray.DataArray`; derives descriptor from
  CF / rioxarray / GeoZarr attrs (priority order below). Internally does
  `await da.isel(y=..., x=...).load_async()` per tile.

`RasterLayer` holds one `TileSource`. `from_geotiff`, `from_zarr`,
`from_xarray` are thin constructors that build the appropriate source and
hand it to `RasterLayer.__init__`.

#### JS side — descriptor-based `RasterModel`

[`src/model/layer/raster.ts`](../../../src/model/layer/raster.ts) currently
receives `_tile_matrix_set` (a TMS object) and builds a
`TileMatrixSetTileset` from it. The change:

- Python serializes a `TilesetDescriptor` via a new trait (`_tileset`).
  TMS, Zarr multiscales, and single-resolution rasters all serialize to
  the same descriptor shape. `_tile_matrix_set` is removed.
- JS derives a `Tileset2D` from the descriptor. For the initial
  implementation this uses `TileMatrixSetTileset` when the descriptor
  looks TMS-shaped, and a new (thin) `DescriptorTileset2D` for the Zarr
  case. The abstraction is internal to `raster.ts`; no public widget
  change.

Reusing deck.gl-raster's upcoming `RasterTileLayer` would eliminate the
hand-rolled wiring in `renderTileMatrixSet`, but that refactor is tracked
separately. This spec preserves the current wiring shape to keep scope
tight.

### Data flow — per-tile

Unchanged from today's GeoTIFF path at the transport level:

1. deck.gl's `TileLayer` asks JS for tile `(x, y, z)`.
2. JS `RasterModel.getTileData` calls
   `invoke(model, {x,y,z}, "raster-get-tile-data", {signal, timeout})`.
3. Python dispatches to the active `TileSource.fetch_tile(x, y, z, signal=...)`.
4. `TileSource.fetch_tile` returns raw tile data (numpy array or
   `async_geotiff.Tile` or `xarray.DataArray`, depending on source).
5. Python passes that to the user's `render_tile(tile) -> EncodedImage`
   callback, returns encoded bytes + media type.
6. JS decodes to `ImageBitmap`, hands to deck.gl-raster's `RasterLayer`.

Source-specific fetch details:

- `ZarrTileSource.fetch_tile`:

  ```python
  async def fetch_tile(self, x, y, z, *, signal=None):
      slice_spec = self._build_slice_spec(x, y, z)  # spatial + pinned non-spatial
      chunk = await self._arr.getitem(slice_spec)  # zarr-python 3 async
      return self._wrap_for_render(chunk)
  ```

- `XarrayTileSource.fetch_tile`:

  ```python
  async def fetch_tile(self, x, y, z, *, signal=None):
      y0, y1, x0, x1 = self._pixel_bounds(x, y, z)
      tile_da = self._da.isel({self._y_dim: slice(y0, y1),
                               self._x_dim: slice(x0, x1)})
      loaded = await tile_da.load_async()  # mutates tile_da in place
      return loaded
  ```

## Public Python API

### `RasterLayer.from_zarr`

```python
@classmethod
def from_zarr(
    cls,
    arr: zarr.AsyncArray | zarr.Array,
    *,
    selection: Mapping[str, int | slice | None],
    render_tile: Callable[[np.ndarray], EncodedImage | None],
    metadata: GeoZarrMetadata | None = None,
    crs: CRS | str | int | None = None,
    transform: Affine | None = None,
    **kwargs,
) -> RasterLayer: ...
```

- `arr` — an opened `zarr.AsyncArray` or sync `zarr.Array`. If a sync
  `Array` is passed, Lonboard accesses `arr._async_array` to get the async
  facade. Caller is responsible for configuring the store (credentials,
  consolidated metadata, range coalescing, etc.).
- `selection` — required. Maps every **non-spatial** dim name to one of:
  an integer (pin to that index), `None` (keep the full extent), or a
  Python `slice` (keep a range). Spatial dims (auto-detected from metadata
  or `arr.metadata.attrs`) MUST NOT appear in `selection`. The selection
  is fixed at layer construction and cannot change interactively in v1.
- `render_tile` — user callback. Receives the numpy array that
  `AsyncArray.getitem(slice_spec)` returns. The array shape matches the
  user's selection (scalar dims are collapsed; kept/slice dims remain).
  Callback returns an `EncodedImage`.
- `metadata` — GeoZarr attrs already parsed (via `@developmentseed/geozarr`
  or equivalent). If `arr` has valid GeoZarr attrs in `arr.attrs`, can be
  omitted.
- `crs` / `transform` — explicit overrides when the store lacks GeoZarr
  metadata entirely (or users want to override detected values). Both must
  be provided together if either is.
- `**kwargs` — standard `RasterLayer` kwargs (`tile_size`, `min_zoom`,
  `max_zoom`, etc.).

Raises `ValueError` at construction if: a non-spatial dim is missing from
`selection`; a spatial dim appears in `selection`; CRS cannot be
determined.

### `RasterLayer.from_xarray`

```python
@classmethod
def from_xarray(
    cls,
    da: xr.DataArray,
    *,
    render_tile: Callable[[xr.DataArray], EncodedImage | None],
    crs: CRS | str | int | None = None,
    transform: Affine | None = None,
    x_dim: str | None = None,
    y_dim: str | None = None,
    **kwargs,
) -> RasterLayer: ...
```

- `da` — an `xarray.DataArray` with at least 2 dims identified as spatial
  (x/y). Users are expected to pin other dims via `.sel()` / `.isel()`
  *before* passing the DataArray in, but v1 does not enforce ndim == 2;
  whatever shape the user hands in is what `render_tile` receives per
  tile (minus the spatial slice).
- `render_tile` — user callback receiving a materialized `xr.DataArray`
  (post-`load_async`). Users can access `.values`, `.coords`, `.attrs`
  from within their callback. Shape matches the DataArray the user
  constructed, with the spatial dims sliced to the tile extent.
- `crs` / `transform` — explicit overrides (see discovery order below).
- `x_dim` / `y_dim` — explicit dim-name overrides if auto-detection fails.
- `**kwargs` — standard `RasterLayer` kwargs.

The DataArray's underlying store MUST support async loading (zarr-python 3,
or any future backend that overrides `BackendArray.async_getitem`). See
[Error handling](#error-handling) for how unsupported backends are
detected — eagerly at construction when possible, with a first-tile
fallback for dask-wrapped or otherwise opaque cases.

### Existing `from_geotiff`

Unchanged at the public API level. Internally refactored onto the new
`TileSource` protocol. No user-visible behavior change.

## CRS & affine discovery (for `from_xarray`)

Priority order, first wins:

1. Explicit `crs=` / `transform=` arguments. Both must be provided together
   if either is. This is the explicit escape hatch.
2. GeoZarr attrs on `da.attrs`: `spatial:transform`, `spatial:shape`,
   `proj:code`, etc., parsed via the same logic as `from_zarr`. Zarr-backed
   DataArrays are the dominant Lonboard use case, and GeoZarr is the
   native convention for describing CRS + affine in Zarr.
3. [rioxarray](https://corteva.github.io/rioxarray/) if installed:
   `da.rio.crs` and `da.rio.transform()`. Handles CF grid_mapping and
   GDAL-style attrs under the hood. Used only if step (2) didn't apply.
4. CF grid_mapping attrs (without rioxarray): `grid_mapping` attr pointing
   to a coordinate variable with `crs_wkt` / `spatial_ref`. Fallback for
   environments that don't have rioxarray installed.
5. If none of the above yields a CRS + transform, raise with a message
   pointing users at the `crs=` / `transform=` arguments.

**Rationale for GeoZarr first:** the motivating use case for `from_xarray`
is users who opened a Zarr store with `xr.open_zarr(...)`. If that store
is GeoZarr-compliant, its attrs already describe the geospatial geometry
correctly; going through rioxarray (which mostly serves GeoTIFF and
CF-NetCDF conventions) adds an indirection that can only lose fidelity.

**rioxarray stays strictly optional — Lonboard MUST NOT add a hard
dependency on rioxarray or (transitively) GDAL.** Import lazily; if
missing, skip step (3) and fall through to CF. Document rioxarray as a
recommended extra for users working with GeoTIFF-derived DataArrays.

## Error handling

Following Lonboard's existing pattern for `from_geotiff` (from
[`_raster.py`](../../../lonboard/layer/_raster.py)):

- Errors raised during `fetch_tile` or `render_tile` are caught, logged to
  the widget's error display (red below the map), and the tile resolves
  as `{"error": ...}` on the wire. JS treats that as a missing tile
  (already implemented in current `RasterModel.getTileData`).
- Construction-time errors (missing selection, bad CRS detection, etc.)
  raise synchronously from the constructor. No partial layer state.
- Backend-async-unsupported: checked eagerly at layer construction when
  possible, with a fallback to first-tile time.

  **Construction-time introspection.** Walk the DataArray's wrapped-array
  chain (`da.variable._data`, then successive `.array` attrs) until
  either an `xarray.backends.common.BackendArray` is found or the walk
  bottoms out. If a `BackendArray` is found and its
  `type(x).async_getitem is BackendArray.async_getitem` (i.e. the base
  class's NotImplementedError-raising default is inherited, not
  overridden), raise immediately with a message naming the backend class
  and explaining that only zarr-python 3 supports async loading today.

  The walk is internal-ish (uses `Variable._data` and `.array` attrs); if
  it can't locate a `BackendArray` — for example, the array is dask-
  wrapped, already computed, or the wrapping structure changed in a
  future xarray version — skip the check silently and let the first-tile
  error path handle it.

  **First-tile fallback.** Any `NotImplementedError` raised from
  `load_async` at tile-fetch time is caught and re-raised with the same
  user-facing message. Defense in depth for cases the construction-time
  check can't handle.

## Testing strategy

- Unit tests for `ZarrTileSource` slice-spec construction: given a
  descriptor, selection, and a tile `(x, y, z)`, assert the correct
  `slice_spec` is produced (including edge tiles with partial bounds).
- Unit tests for `XarrayTileSource` CRS/transform discovery across the
  priority order above. Mock the rioxarray accessor; use synthetic
  DataArrays with CF and GeoZarr attrs.
- Integration tests with a small fixture Zarr store checked into
  `tests/fixtures/` (or generated at test time). Open it, construct a
  `RasterLayer.from_zarr`, assert the `TilesetDescriptor` traitlet
  payload matches an expected shape.
- Manual / notebook-driven end-to-end test against the Dynamical.org
  ECMWF store (same as the JS example). Used as the documentation
  notebook.

## Documentation

- New notebook: `examples/zarr-ecmwf.ipynb` (or similar), mirroring the
  JS example but via `RasterLayer.from_xarray`.
- New blog post section / follow-up to `initial-cog.md` introducing
  Zarr support.
- API reference updates in mkdocs for the two new constructors.

## Future work (explicitly deferred)

- **Animation over non-spatial dims.** Requires either (a) per-frame tile
  re-requests (cheap to build, slow to animate) or (b) Python → WebGL DSL
  to hoist the animation dim into a GPU uniform. Blocked on (b)'s
  infrastructure, which is planned separately.
- **WebGL-side rendering.** Raw Zarr chunks transferred from Python as
  binary buffers and rendered via deck.gl-raster's shader pipeline. Again
  blocks on the Python → WebGL DSL work.
- **Client-side Zarr fetching.** Using `@developmentseed/deck.gl-zarr`
  directly, bypassing Python. Valuable for public, unauthenticated Zarr
  stores where the Python proxy is pure overhead. Not in v1.
- **`RasterTileLayer` adoption.** When the deck.gl-raster refactor lands,
  Lonboard's `raster.ts` shrinks considerably. Tracked in a separate spec.
- **Concurrency limiting on the Python side.** Semaphore around
  `fetch_tile` if we observe overload. Not needed for v1 given deck.gl's
  `maxRequests` cap.

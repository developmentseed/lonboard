# `RasterLayer.from_xarray` design

Updates the April design (`dev-docs/superpowers/specs/2026-04-23-lonboard-zarr-support-design.md`
on branch `feat/zarr-support`). Its reasoning on why Python fetches still
holds. Its architecture section is replaced by this document: `RasterTileLayer`
has landed, and the existing `_fetch_tile` / `_render_tile` callables are the
tile-source abstraction, so no `TileSource` class is added.

## Goal

```python
layer = RasterLayer.from_xarray(da, render_tile=...)
```

A 2-D (or band, y, x) `xarray.DataArray` on a regular grid, or a `DataTree`
holding a GeoZarr multiscale pyramid, shows up on the map the way
`from_geotiff` does today: the browser asks for a tile, Python reads that
window, `render_tile` encodes it, the browser draws it. Static encoded tiles
are the complete first result. `xarray` stays an optional dependency.

Non-goals: GPU styling of data pixels, animation over extra dimensions,
browser-side Zarr, changes to deck.gl-raster.

## What exists, checked at `41f9e99b`

- Python: `RasterLayer.__init__` takes `_tile_matrix_set`, `_crs`,
  `_fetch_tile`, `_render_tile`, `_bounds`, `_center`. The wire protocol is a
  tagged union (`empty`, `encoded-image`, error).
- Browser: `RasterModel` builds a `TileMatrixSetAdaptor` when
  `_tile_matrix_set` is set, else falls back to Web Mercator `TileLayer`.
- deck.gl-raster 0.8.1 (already installed) exports `AffineTileset` and
  `AffineTilesetLevel`. A level is `{affine: [a,b,c,d,e,f], arrayWidth,
  arrayHeight, tileWidth, tileHeight, mpu}`, affine maps pixel edges to CRS,
  levels ordered coarsest first. Tile size is free per level, so the grid does
  not need to match any internal chunking.
- Traversal: with a single level, every visible level-0 tile is selected no
  matter how far out the view is. `min_zoom` returns no tiles below a viewport
  zoom. Edge tiles may be smaller than the tile size; `RasterTileLayer` uses
  the returned image's width and height, which is how `from_geotiff` already
  works.
- xarray (checked 2026.9.0): `DataArray.load_async` exists since 2025.8.0. It is
  only truly async for lazily indexed backend arrays whose backend overrides
  `async_getitem`, which today is Zarr alone; netCDF backends raise
  `NotImplementedError`, and dask or numpy data is computed synchronously on
  the event loop. A strided `isel` on a lazy Zarr array stays lazy and loads
  only the selected samples' chunks.
- rioxarray refuses dims named `lat`/`lon` (`MissingSpatialDimensionError`)
  and writes the CRS as a CF `spatial_ref` coordinate with `grid_mapping` in
  `encoding`. xarray's own CF decoding puts `grid_mapping` in `encoding` with
  `decode_coords="all"`, otherwise in `attrs` and the `spatial_ref` variable
  is not attached to the DataArray at all.

## Approaches considered

1. **Extend the existing callables and send an affine grid (chosen).** A new
   private trait carries affine levels; the browser builds an `AffineTileset`
   from it; `from_xarray` is a constructor that builds the levels, a
   `_fetch_tile` and a `_render_tile`. Smallest diff, nothing new to learn,
   `from_geotiff` and `from_pmtiles` untouched.
2. **A `TileSource` protocol class** (the April design). Adds a class
   hierarchy and a refactor of `from_geotiff` for no behavior the callables
   don't already give. Rejected.
3. **Generalize `_tile_matrix_set`** by generating a TMS from the array.
   Would work for axis-aligned grids but forces every future source through
   morecantile and the TMS model. Rejected; the affine grid is the simpler,
   more general description and deck.gl-raster already has it.
4. **A browser-side `RasterSource`** (deck.gl-raster 0.10). That class holds
   a descriptor and WGS84 bounds, and its subclasses (`COGSource`,
   `ZarrSource`) open data in the browser and read tiles from it. Lonboard
   opens data in Python, so it has one browser construct: a descriptor plus
   a `getTileData` that round-trips through the widget. `RasterTileLayer`
   takes those as props directly. Nothing to wrap now; if a later layer only
   accepts a `RasterSource`, a two-field subclass can hold the same
   descriptor and bounds without changing the Python side.

## Design

### Step 1: affine grid trait (no user-facing change)

Python, in `lonboard/raster/_models.py`:

```python
@dataclass(frozen=True)
class AffineLevel:
    """One resolution level of a raster grid, from pixel edges to CRS."""
    transform: Affine   # affine.Affine
    width: int          # array width in pixels
    height: int
    tile_width: int
    tile_height: int
```

`transform` is an [`affine.Affine`](https://github.com/rasterio/affine), the
type rasterio, rioxarray and async-geotiff already use. The `affine` package
is pure Python and BSD-licensed; it is not a core dependency, so it is listed
in the `xarray` extra (the `geotiff` extra already brings it through
async-geotiff) and imported only where levels are built or validated. A new
`AffineLevelsTrait` in `lonboard/traits/_raster.py` validates a
`list[AffineLevel]`, coarsest first, and serializes each level as
`{affine, arrayWidth, arrayHeight, tileWidth, tileHeight, mpu}`, the exact
field names of `AffineTilesetLevelOptions`, with `affine` as
`list(transform)[:6]`, the `[a, b, c, d, e, f]` the browser's `Affine` type
is. The browser constructs levels with no mapping. `mpu` (meters per CRS unit) is computed in Python from the
`_crs` with pyproj, following morecantile's rule: metre 1, degree
2πa/360, foot 0.3048. That is about eight lines and avoids importing
morecantile.

`RasterLayer.__init__` gains `_affine_levels: list[AffineLevel] | None = None`.
Exactly one of `_tile_matrix_set` and `_affine_levels` may be set; the
constructor raises otherwise.

Browser, `src/model/layer/raster.ts`: `render()` checks `_affine_levels`
first and builds `new AffineTileset({levels: levels.map(l => new
AffineTilesetLevel(l)), ...projection fns})`, then the existing TMS path,
then the fallback. The `RasterTileLayer` construction is shared between the
two descriptor paths.

Tests: Python trait round trip (input forms, ordering, mutual exclusion with
TMS); Vitest for the model building an `AffineTileset` from a serialized
level list with the fake widget model.

### Step 2: `RasterLayer.from_xarray`

```python
@staticmethod
def from_xarray(
    data: xr.DataArray | xr.DataTree,
    /,
    *,
    render_tile: RenderTile[xr.DataArray],
    variable: str | None = None,
    crs: CRS | str | int | None = None,
    transform: Affine | None = None,
    tile_size: int | None = None,
    **kwargs: Unpack[RasterLayerKwargs],
) -> RasterLayer[xr.DataArray]:
```

A `DataArray` is one level. A `DataTree` is a GeoZarr multiscale pyramid
(step 3). `variable` names the data variable inside a tree's level groups,
required when a group has more than one. `tile_size=None` follows the data's
chunking; an integer fixes the tile. Step 2 builds the `DataArray` path and
step 3 adds the tree; the signature is settled here so step 3 adds no
argument.

Lives in a new module `lonboard/layer/_raster_xarray.py` (lazy imports of
xarray and affine), called from a thin `from_xarray` on `RasterLayer`, same
as the other constructors. A new extra
`xarray = ["xarray>=2025.1", "affine>=2.4"]` in `pyproject.toml`.

**Spatial dims.** The last two dims are `(y, x)`, the numpy and rasterio
convention. The array must have two or three dims; a leading dim (bands) is
passed through to `render_tile` untouched. Four or more dims raise
`ValueError("... select down to (y, x) or (band, y, x) with .isel()/.sel()")`.
No `x_dim`/`y_dim` kwargs; `transpose` is the escape hatch.

**Transform.** From the two 1-D coordinates: `step = (last - first) /
(n - 1)`, origin `first - step/2` (CF coordinates are cell centers), and a
regularity check `np.allclose(np.diff(coord), step, rtol=1e-6)`. A
descending `y` gives `e < 0` (north-up); ascending gives `e > 0`, which
`AffineTilesetLevel` handles as any other affine (bounds come from the four
corners). A missing or irregular coordinate raises
`ValueError("Coordinate 'lat' is not evenly spaced (spacing ranges from a to
b). from_xarray needs a regular grid; pass transform= or resample.")`.
`transform=` overrides all of this.

**CRS.** `crs=` (anything `ProjectionTrait` accepts) wins outright.
Otherwise a private list of finders, each `(da) -> CRS | None`, is tried in
order and the first hit wins. Each metadata model is one function in that
list, so supporting another model is adding a function, and no model is
built into the rest of the code. The first iteration ships two:

1. GeoZarr attrs on the array: `proj:code`, else `proj:wkt2`, else
   `proj:projjson`, through `pyproj.CRS.from_user_input`. This is the model
   deck.gl-zarr's `ZarrSource` reads.
2. Geographic heuristic: the x coordinate is named `x`, `lon` or `longitude`
   or has `units` `degrees_east`, and y likewise with `lat`/`latitude`/
   `degrees_north`: `EPSG:4326`.

No hit raises `ValueError` naming `crs=`.

A CF finder is a separate small PR after the first demo works: the
coordinate named by `da.encoding["grid_mapping"]` or `da.attrs["grid_mapping"]`,
else one called `spatial_ref`, with its attrs passed to `pyproj.CRS.from_cf`.
pyproj does the convention work. It matters because xarray, rioxarray and
GDAL all write a CRS that way, and its error should suggest
`decode_coords="all"`, since without it xarray drops the `spatial_ref`
variable. rioxarray itself is not consulted: it would add an optional import
for data the CF finder handles, and it rejects `lat`/`lon` dims.

**Longitude 0 to 360.** If the CRS is geographic and the x coordinate
exceeds 180, the array is rolled lazily:
`da.assign_coords(x=((x + 180) % 360) - 180).sortby(x)`. `sortby` is an
integer indexer that stays lazy on Zarr and dask, so it costs nothing until a
tile is read. ERA5 and xarray's tutorial `air_temperature` are 0 to 360, so
this is worth the five lines.

**Levels.** The layer holds `levels: list[xr.DataArray]`, coarsest first,
one `AffineLevel` each. A `DataArray` input is a single level. Python builds
no pyramid of its own: decimating or coarsening a lazy store in Python would
read every chunk under a coarse tile, up to the whole array for the coarsest
one, which is the unintended fetch this design must avoid. Coarse levels
come from the data (a multiscale tree, step 3). `fetch_tile(x, y, z)` slices
`levels[z]` by the tile window and loads it, the same code for one level or
ten.

**Zoomed-out views and `min_zoom`.** With a single level, deck.gl-raster
requests every visible level-0 tile however far out the view is, so
`from_xarray` sets a default `min_zoom` when the caller passes none. It is
the Web Mercator viewport zoom at which one coarsest-level tile covers at
least a quarter of its pixel size on screen, computed at the data's center
latitude:

```
screen_mpp(z) = 156543.03 * cos(lat_center) / 2**z
min_zoom = ceil(log2(156543.03 * cos(lat_center) / (coarsest_mpp * 4)))
```

where `coarsest_mpp` is the coarsest level's meters per pixel (`AffineLevel`
pixel size times `mpu`). A 512 px tile is then at least 128 screen pixels, so
a 1920 by 1080 viewport asks for at most about 15 by 9 tiles; a multiscale
tree whose coarsest level fits one tile gets `min_zoom` 0. Below `min_zoom`
deck.gl-raster draws nothing; `min_zoom=` overrides the default. A
"zoom in to see the data" notice, as deck.gl-raster's own examples show, is
later work.

**Tile size follows the chunks** unless `tile_size` is given, in which case
the tile is that many pixels square. Chunk sizes for the two spatial dims come
from, in order: dask chunks (`da.chunksizes`) when every chunk on an axis is
the same size except possibly the last; else the store's chunks that xarray
records on a lazily opened array (`da.encoding["preferred_chunks"]`, which is
how Zarr chunking reaches a non-dask DataArray); else none. With chunks, the
tile on each axis is the chunk size times the smallest whole number that
makes it at least 256 px, so a tile is always a whole number of chunks and a
64 px chunk does not become a 64 px tile. If that exceeds 2048 px on either
axis, or there are no chunks, the tile is 512 by 512. Tiles may be
non-square; `AffineTilesetLevel` takes width and height separately. Each
level picks its own tile size from its own chunks. The chosen tile size is
recorded on each `AffineLevel`; `RasterLayer`'s `_tile_size` trait is the
rendering hint deck.gl uses for zoom and is left alone.

**Loading.** Two paths, chosen with public API only. If `da.chunks is None`
the array is in memory or lazily indexed by a backend, and `fetch_tile`
starts with `await window.load_async()`: a no-op for in-memory data, native
async for Zarr. If that raises `NotImplementedError` (netCDF and any backend
without `async_getitem`), the layer records it and every later tile, and
that one, uses `await asyncio.to_thread(window.load)`. Dask-backed arrays
(`da.chunks` set) always take the thread path, because `load_async` computes
dask on the event loop. Rendering stays on the loop as it does today.
Tests cover each path with an in-memory array, a lazily opened in-memory
Zarr store, a dask array, and a stub backend array whose `async_getitem`
raises.

**Bounds and center.** The coarsest level's corners through its transform,
reprojected to WGS84 with pyproj, as `from_geotiff` does.

**Missing values.** Edge tiles are partial, same as today. Values are
whatever xarray decoded: NaN for masked floats, or raw integers with
`_FillValue` in `attrs` when `mask_and_scale=False`. The user's
`render_tile` owns transparency; the docs show the NaN-to-alpha pattern.

Tests (`tests/test_raster_xarray.py`, `importorskip("xarray")`): transform
from descending and ascending coordinates, irregular coordinate error, each
CRS finder and the no-hit error, the 0 to 360 roll, the single level's
transform and sizes, the default `min_zoom` for a small and a large array and
that `min_zoom=` overrides it, `fetch_tile` windows at interior and edge
tiles, extra-dim errors, and tile size from dask chunks, from a lazily opened
Zarr store's chunks (in-memory `zarr` store, `importorskip("zarr")`), from
small chunks rounded up to a multiple, from oversized chunks, from no chunks,
and from `tile_size=`. A UI test beside `tests/ui/test_raster.py` with a
solid-color in-memory array checks that tiles render.

### Step 3: multiscale `DataTree`

`from_xarray` accepts a `DataTree` opened with `xr.open_datatree(store,
engine="zarr")` from a GeoZarr multiscale group, the layout deck.gl-zarr's
`ZarrSource` reads (checked against `@developmentseed/geozarr` 0.10 and a
store built by hand): the root group's attrs hold `spatial:dimensions`,
`proj:*` and `multiscales.layout`, a finest-first list of items with an
`asset` (the child group's path) and optional `spatial:transform` and
`spatial:shape`; each child group holds the variable at that resolution with
its own coordinates and chunks. Verified with xarray 2026.9.0: the root's
attrs and children come through, each level's `encoding["preferred_chunks"]`
is the store's chunking, and the levels' coordinates are cell centers.

Each layout item's `asset` names either a child group (the level's variable
is `variable`, or the group's only data variable) or, in the array-based
form the convention also allows, a data variable on the root itself, which
is how xarray presents a group whose levels are bare arrays. The levels are
those DataArrays in layout order, reversed to coarsest first. Each level's
transform is the layout item's `spatial:transform` if present, else from
its coordinates as for a single array; a level with neither is an error
naming both. Tile size comes from each level's own chunks; the CRS from the
finders run on the root's attrs (the GeoZarr finder hits `proj:code`).
Everything after that, `fetch_tile`, loading, bounds and `min_zoom`, is the
single-array code over a longer list. A tree with no `multiscales` attr is
an error naming the convention.

Tests: a two-level store built in memory as above; level order, per-level
transforms and tile sizes, the `variable` rule, and a `fetch_tile` at each
level.

### Step 4: example notebook and docs page

The demo dataset is carbonplan's USGS CONUS 10 m DEM pyramid, the default
dataset of carbonplan/zarr-layer (MIT):
`https://carbonplan-share.s3.us-west-2.amazonaws.com/zarr-layer-examples/USGS-CONUS-DEM-10m.zarr`.
Checked on 2026-11-13: Zarr v3 with consolidated metadata, so
`xr.open_datatree(store, engine="zarr", consolidated=True)` works over plain
HTTP with no listing and no credentials. The root holds `proj:code`
EPSG:4326 and a `multiscales.layout` in the current convention (finest
first, relative scales, no `spatial:transform`), with fourteen child groups
`0` to `13`. Each level has `DEM`, `hillshade`, `aspect` and `slope` as
float32 over `(latitude, longitude)`, descending latitude, evenly spaced
coordinates, a CF `spatial_ref` coordinate, and its own chunking (362 by
362 at level 0, which is 262913 by 636928 pixels; coarse levels are one or
a few chunks). It exercises every rule in steps 2 and 3 without a CF
finder: `proj:code` at the root, transform from coordinates, tiles from
chunks, `variable=` because each group has four. The notebook opens it,
picks `hillshade` or `DEM`, and shows it with a colormap `render_tile`
that makes NaN transparent.

Two other public stores were checked and are not usable as-is. The
geozarr-examples Sentinel-2 store at
`s3://us-west-2.opendata.source.coop/pangeo/geozarr-examples/TCI.zarr` has
the layout but its arrays lack `dimension_names`, which xarray requires;
the draft PR developmentseed/geozarr-examples#36 fixes that locally.
carbonplan's older ndpyramid stores (`multiscales: [{datasets: [{path,
pixels_per_tile, crs}]}]`, CF `spatial_ref` per level) open fine in xarray
but use a different layout; reading it would be a second layout parser,
later, if wanted.
Docs: the notebook added to `mkdocs.yml`; `from_xarray` appears on the
existing `RasterLayer` API page through mkdocstrings.

### Step 5, if time remains

**CF CRS finder.** The `grid_mapping` function described above, added to
the finder list, with tests on rioxarray-written and xarray-written data.

**Default renderer.** `render_tile` becomes optional for 2-D arrays:
`vmin`/`vmax` (default: min and max of the coarsest level, which is already
loaded cheaply), `cmap` (palettable or matplotlib, through the existing
`apply_continuous_cmap`; grayscale when `None`), NaN and `_FillValue` to
alpha 0, PNG encoding through a lazy pillow import with a clear error.

**`from_zarr`** wraps a `zarr.Array` or group with the same levels, using
GeoZarr `spatial:transform` and `proj:code` attrs for the grid, `arr.chunks`
for tile size, and `AsyncArray.getitem` for a native async read.

**Zoom notice.** A small overlay in the widget when the view is below the
layer's `min_zoom`, like deck.gl-raster's example `ZoomNotice`.

**Sub-chunk tiles.** The first iteration makes a tile a whole number of
chunks. Whether a tile should instead be a fraction of a large chunk, and
how that interacts with the browser's tile size hint, is a follow-up
decision once real stores have been tried.

## Forward compatibility

Fetching and rendering stay separate callables. The reply stays a tagged
union. The grid trait says nothing about xarray. Nothing is built for GPU
styling.

## Left to the builder

Exact error wording, the name of the trait (`_affine_levels` suggested), test
fixtures, and whether `mpu` is sent per level or once (per level mirrors
deck.gl-raster and keeps the browser code to a `map`).

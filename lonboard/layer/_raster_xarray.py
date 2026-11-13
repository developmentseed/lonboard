"""Build a `RasterLayer` from xarray data.

Everything here works over a list of levels, coarsest first, so one array and a
multiscale pyramid share the same tile fetching.
"""

from __future__ import annotations

import asyncio
import math
from typing import TYPE_CHECKING, Any

import numpy as np
from pyproj import CRS
from pyproj.transformer import Transformer

from lonboard._geoarrow.ops import Bbox
from lonboard.raster import AffineLevel

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Mapping

    import xarray as xr
    from affine import Affine

    from lonboard.layer._raster import FetchTile, RasterLayer, RenderTile


def spatial_dims(da: xr.DataArray) -> tuple[Hashable, Hashable]:
    """Return the `(y, x)` dims of `da`: its last two.

    A leading band dim is allowed; anything more must be selected away first.
    """
    if da.ndim not in (2, 3):
        raise ValueError(
            f"Expected a 2-D (y, x) or 3-D (band, y, x) DataArray, got {da.ndim} dims "
            f"{tuple(da.dims)}. Select down with .isel() or .sel() first.",
        )

    return da.dims[-2], da.dims[-1]


def _is_regular(values: np.ndarray, step: float) -> bool:
    """Whether `values` are evenly spaced by `step`, within the precision of their dtype."""
    diffs = np.diff(values.astype("f8"))
    atol = abs(step) * 1e-6
    if np.issubdtype(values.dtype, np.floating):
        # float32 coordinates carry about seven digits, so a 0.1 degree step at
        # longitude 179 is only exact to 1e-5 or so.
        atol = max(atol, 8 * np.finfo(values.dtype).eps * float(np.abs(values).max()))
    return bool(np.allclose(diffs, step, rtol=1e-6, atol=atol))


def _regular_step(da: xr.DataArray, dim: Hashable) -> float:
    """Return the spacing of the 1-D coordinate on `dim`; raise if it is missing or uneven."""
    if dim not in da.coords:
        raise ValueError(
            f"Coordinate {dim!r} is missing. from_xarray needs 1-D coordinates on "
            "the spatial dims; pass transform= to give the grid directly.",
        )

    values = np.asarray(da[dim].values)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(
            f"Coordinate {dim!r} must be 1-D with at least two values to find the "
            "pixel size; pass transform= to give the grid directly.",
        )

    step = float((float(values[-1]) - float(values[0])) / (len(values) - 1))
    if not _is_regular(values, step):
        diffs = np.diff(values.astype("f8"))
        raise ValueError(
            f"Coordinate {dim!r} is not evenly spaced (spacing ranges from "
            f"{diffs.min()} to {diffs.max()}). from_xarray needs a regular grid; "
            "pass transform= or resample.",
        )

    return step


def coordinate_transform(
    da: xr.DataArray,
    y_dim: Hashable,
    x_dim: Hashable,
) -> Affine:
    """Return the pixel-edge to CRS affine from the cell-center coordinates of `da`."""
    from affine import Affine

    step_y = _regular_step(da, y_dim)
    step_x = _regular_step(da, x_dim)
    x0 = float(da[x_dim].values[0]) - step_x / 2
    y0 = float(da[y_dim].values[0]) - step_y / 2
    return Affine(step_x, 0.0, x0, 0.0, step_y, y0)


def geozarr_crs_from_attrs(attrs: Mapping[str, Any]) -> CRS | None:
    """Return the CRS from GeoZarr `proj:code`, `proj:wkt2` or `proj:projjson` attrs."""
    if "proj:code" in attrs:
        return CRS.from_user_input(attrs["proj:code"])
    if "proj:wkt2" in attrs:
        return CRS.from_wkt(attrs["proj:wkt2"])
    if "proj:projjson" in attrs:
        return CRS.from_json_dict(attrs["proj:projjson"])
    return None


def geozarr_crs(da: xr.DataArray) -> CRS | None:
    """Return the CRS from the GeoZarr `proj:*` attrs of `da`."""
    return geozarr_crs_from_attrs(da.attrs)


_LON_NAMES = {"lon", "longitude"}
_LAT_NAMES = {"lat", "latitude"}


def _is_axis(da: xr.DataArray, dim: Hashable, names: set[str], units: str) -> bool:
    if str(dim).lower() in names:
        return True
    coord = da.coords.get(dim)
    return coord is not None and coord.attrs.get("units") == units


def geographic_crs(da: xr.DataArray) -> CRS | None:
    """Return EPSG:4326 when the spatial dims look like longitude and latitude."""
    y_dim, x_dim = da.dims[-2], da.dims[-1]
    if _is_axis(da, x_dim, _LON_NAMES, "degrees_east") and _is_axis(
        da,
        y_dim,
        _LAT_NAMES,
        "degrees_north",
    ):
        return CRS.from_epsg(4326)
    return None


CRS_FINDERS: list[Callable[[xr.DataArray], CRS | None]] = [
    geozarr_crs,
    geographic_crs,
]
"""Ways to find a DataArray's CRS, tried in order. Each metadata model is one function."""


def find_crs(da: xr.DataArray) -> CRS:
    """Return the CRS of `da` from the first finder in `CRS_FINDERS` that knows it."""
    for finder in CRS_FINDERS:
        crs = finder(da)
        if crs is not None:
            return crs

    raise ValueError(
        "Could not find a CRS: no GeoZarr proj:* attrs and the spatial dims are not "
        "named like longitude/latitude. Pass crs= (for example crs='EPSG:4326').",
    )


def roll_longitude(da: xr.DataArray, x_dim: Hashable) -> xr.DataArray:
    """Move a 0 to 360 longitude coordinate to -180 to 180, lazily.

    Left alone when there is no coordinate, or when rolling would split the
    grid (a region that straddles 180).
    """
    if x_dim not in da.coords:
        return da
    lon = da[x_dim]
    if float(lon.max()) <= 180:
        return da

    rolled = da.assign_coords({x_dim: ((lon + 180) % 360) - 180}).sortby(x_dim)
    values = np.asarray(rolled[x_dim].values)
    step = (float(values[-1]) - float(values[0])) / (len(values) - 1)
    if not _is_regular(values, step):
        return da
    return rolled


_MIN_TILE = 256
_MAX_TILE = 2048
_DEFAULT_TILE = 512


def _regular_chunk(da: xr.DataArray, dim: Hashable) -> int | None:
    """Return the chunk size on `dim` when chunks are regular, else `None`.

    Dask chunks win when present (they are what gets read); otherwise the
    store's chunks that xarray records on a lazily opened array.
    """
    if da.chunks is not None:
        sizes = da.chunksizes[dim]
        if len(set(sizes[:-1])) <= 1 and sizes[-1] <= sizes[0]:
            return int(sizes[0])
        return None

    preferred = da.encoding.get("preferred_chunks", {}).get(dim)
    return int(preferred) if preferred else None


def chunk_tile_size(
    da: xr.DataArray,
    y_dim: Hashable,
    x_dim: Hashable,
    tile_size: int | None,
) -> tuple[int, int]:
    """Return `(tile_width, tile_height)` for `da`.

    An explicit `tile_size` is used square. Otherwise a tile is a whole number
    of chunks, at least 256 px; without chunks, or past 2048 px, it is 512 px.
    """
    if tile_size is not None:
        return tile_size, tile_size

    def from_chunk(dim: Hashable) -> int:
        chunk = _regular_chunk(da, dim)
        if chunk is None:
            return _DEFAULT_TILE
        tile = chunk * math.ceil(_MIN_TILE / chunk)
        return tile if tile <= _MAX_TILE else _DEFAULT_TILE

    return from_chunk(x_dim), from_chunk(y_dim)


def level_for(
    da: xr.DataArray,
    y_dim: Hashable,
    x_dim: Hashable,
    transform: Affine,
    tile: tuple[int, int],
) -> AffineLevel:
    """Return the `AffineLevel` describing `da` with the given grid and `(tile_width, tile_height)`."""
    return AffineLevel(
        transform=transform,
        width=int(da.sizes[x_dim]),
        height=int(da.sizes[y_dim]),
        tile_width=tile[0],
        tile_height=tile[1],
    )


def wgs84_bounds(level: AffineLevel, crs: CRS) -> Bbox:
    """Return the WGS84 bounding box of a level's array."""
    t = level.transform
    corners = [
        t * (0, 0),
        t * (level.width, 0),
        t * (0, level.height),
        t * (level.width, level.height),
    ]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    return Bbox(*transformer.transform_bounds(min(xs), min(ys), max(xs), max(ys)))


# Web Mercator meters per CSS pixel at zoom 0 on the equator.
_ZOOM0_METERS_PER_PIXEL = 156543.03

# Below the default min_zoom a tile would be smaller than this fraction of its
# pixel size on screen, so a viewport would ask for too many tiles.
_MIN_TILE_SCREEN_FRACTION = 1 / 4


def default_min_zoom(level: AffineLevel, mpu: float, center_lat: float) -> int:
    """Return the viewport zoom below which the coarsest level is not requested.

    At that zoom one tile of `level` covers at least a quarter of its pixel
    size on screen, measured at `center_lat`.
    """
    t = level.transform
    pixel_meters = math.sqrt(abs(t.a * t.e)) * mpu
    screen_meters_per_pixel = _ZOOM0_METERS_PER_PIXEL * math.cos(
        math.radians(center_lat),
    )
    zoom = math.log2(screen_meters_per_pixel * _MIN_TILE_SCREEN_FRACTION / pixel_meters)
    return max(0, math.ceil(zoom))


def _layout_items(tree: xr.DataTree) -> list[dict[str, Any]]:
    """Return the `multiscales.layout` items of a GeoZarr multiscale group."""
    try:
        items = tree.attrs["multiscales"]["layout"]
    except (KeyError, TypeError):
        items = None
    if not isinstance(items, list) or not items:
        raise ValueError(
            "Expected a GeoZarr multiscale group: the root attrs need a 'multiscales' "
            "dict with a non-empty 'layout' list (the zarr-conventions multiscales "
            "convention).",
        )
    return items


def _level_array(tree: xr.DataTree, asset: str, variable: str | None) -> xr.DataArray:
    """Return the array that a layout item's `asset` names: a group's variable, or an array."""
    import xarray as xr

    try:
        node = tree[asset]
    except KeyError as e:
        raise ValueError(
            f"multiscales layout asset {asset!r} is not a group or array in the tree",
        ) from e

    if isinstance(node, xr.DataArray):
        return node

    ds = node.to_dataset()
    names = list(ds.data_vars)
    if variable is not None:
        if variable not in ds.data_vars:
            raise ValueError(
                f"Level {asset!r} has no variable {variable!r}; it has {names}",
            )
        return ds[variable]
    if len(names) != 1:
        raise ValueError(
            f"Level {asset!r} has variables {names}; pass variable= to pick one",
        )
    return ds[names[0]]


def _level_transform(da: xr.DataArray, item: dict[str, Any]) -> Affine:
    """Return a level's transform: the item's `spatial:transform`, else from its coordinates."""
    from affine import Affine

    transform = item.get("spatial:transform")
    if transform is not None:
        return Affine(*(float(v) for v in transform[:6]))

    try:
        return coordinate_transform(da, *spatial_dims(da))
    except ValueError as e:
        raise ValueError(
            f"Level {item['asset']!r} has no 'spatial:transform' in the multiscales "
            f"layout and its coordinates do not give a grid: {e}",
        ) from e


def multiscale_levels(
    tree: xr.DataTree,
    variable: str | None,
) -> list[tuple[xr.DataArray, Affine]]:
    """Return `(array, transform)` per level of a GeoZarr multiscale tree, coarsest first."""
    levels = []
    for item in _layout_items(tree):
        da = _level_array(tree, item["asset"], variable)
        levels.append((da, _level_transform(da, item)))

    return sorted(levels, key=lambda level: -math.hypot(level[1].a, level[1].d))


class WindowLoader:
    """Load tile windows without blocking the event loop.

    Starts with `load_async` when `use_async` is set, and switches to a thread
    for good the first time the backend raises `NotImplementedError`.
    """

    def __init__(self, *, use_async: bool) -> None:
        self.use_async = use_async

    async def load(self, window: xr.DataArray) -> xr.DataArray:
        """Return `window` with its data in memory."""
        if self.use_async:
            try:
                return await window.load_async()
            except NotImplementedError:
                self.use_async = False

        return await asyncio.to_thread(window.load)


def make_fetch_tile(
    levels: list[xr.DataArray],
    affine_levels: list[AffineLevel],
    y_dim: Hashable,
    x_dim: Hashable,
    loader: WindowLoader,
) -> FetchTile[xr.DataArray]:
    """Return a `fetch_tile` that reads tile `(x, y)` of `levels[z]`."""

    async def fetch_tile(x: int, y: int, z: int) -> xr.DataArray:
        level = affine_levels[z]
        window = levels[z].isel(
            {
                y_dim: slice(y * level.tile_height, (y + 1) * level.tile_height),
                x_dim: slice(x * level.tile_width, (x + 1) * level.tile_width),
            },
        )
        return await loader.load(window)

    return fetch_tile


def build_from_xarray(  # noqa: PLR0913
    data: Any,
    *,
    render_tile: RenderTile[xr.DataArray],
    variable: str | None = None,  # noqa: ARG001
    crs: Any = None,
    transform: Affine | None = None,
    tile_size: int | None = None,
    **kwargs: Any,
) -> RasterLayer[xr.DataArray]:
    """Build a `RasterLayer` from a `DataArray`. See `RasterLayer.from_xarray`."""
    import xarray as xr

    from lonboard.layer._raster import RasterLayer
    from lonboard.traits._raster import meters_per_unit

    if not isinstance(data, xr.DataArray):
        raise TypeError(
            f"from_xarray expects an xarray.DataArray, got {type(data).__name__}",
        )

    da = data
    y_dim, x_dim = spatial_dims(da)
    if _is_axis(da, y_dim, _LON_NAMES, "degrees_east") and _is_axis(
        da,
        x_dim,
        _LAT_NAMES,
        "degrees_north",
    ):
        raise ValueError(
            f"The last two dims {(y_dim, x_dim)} look like (longitude, latitude); "
            f"from_xarray expects (y, x). Transpose with "
            f".transpose(..., {x_dim!r}, {y_dim!r}).",
        )
    crs = CRS.from_user_input(crs) if crs is not None else find_crs(da)
    if transform is None:
        if crs.is_geographic:
            da = roll_longitude(da, x_dim)
        transform = coordinate_transform(da, y_dim, x_dim)

    level = level_for(
        da,
        y_dim,
        x_dim,
        transform,
        chunk_tile_size(da, y_dim, x_dim, tile_size),
    )
    bounds = wgs84_bounds(level, crs)
    center = ((bounds.minx + bounds.maxx) / 2, (bounds.miny + bounds.maxy) / 2)
    kwargs.setdefault(
        "min_zoom",
        default_min_zoom(level, meters_per_unit(crs), center[1]),
    )

    loader = WindowLoader(use_async=da.chunks is None)
    return RasterLayer(
        _tile_matrix_set=None,
        _affine_levels=[level],
        _crs=crs,
        _fetch_tile=make_fetch_tile([da], [level], y_dim, x_dim, loader),
        _render_tile=render_tile,
        _bounds=bounds,
        _center=center,
        **kwargs,
    )

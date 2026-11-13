"""Build a `RasterLayer` from xarray data.

Everything here works over a list of levels, coarsest first, so one array and a
multiscale pyramid share the same tile fetching.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from pyproj import CRS

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable

    import xarray as xr
    from affine import Affine


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


def _regular_step(da: xr.DataArray, dim: Hashable) -> float:
    """Return the spacing of the 1-D coordinate on `dim`; raise if it is missing or uneven."""
    if dim not in da.coords:
        raise ValueError(
            f"Coordinate {dim!r} is missing. from_xarray needs 1-D coordinates on "
            "the spatial dims; pass transform= to give the grid directly.",
        )

    values = np.asarray(da[dim].values, dtype="f8")
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(
            f"Coordinate {dim!r} must be 1-D with at least two values to find the "
            "pixel size; pass transform= to give the grid directly.",
        )

    step = (values[-1] - values[0]) / (len(values) - 1)
    diffs = np.diff(values)
    if not np.allclose(diffs, step, rtol=1e-6, atol=abs(step) * 1e-6):
        raise ValueError(
            f"Coordinate {dim!r} is not evenly spaced (spacing ranges from "
            f"{diffs.min()} to {diffs.max()}). from_xarray needs a regular grid; "
            "pass transform= or resample.",
        )

    return float(step)


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


def geozarr_crs(da: xr.DataArray) -> CRS | None:
    """Return the CRS from GeoZarr `proj:code`, `proj:wkt2` or `proj:projjson` attrs."""
    attrs = da.attrs
    if "proj:code" in attrs:
        return CRS.from_user_input(attrs["proj:code"])
    if "proj:wkt2" in attrs:
        return CRS.from_wkt(attrs["proj:wkt2"])
    if "proj:projjson" in attrs:
        return CRS.from_json_dict(attrs["proj:projjson"])
    return None


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
    """Move a 0 to 360 longitude coordinate to -180 to 180, lazily."""
    lon = da[x_dim]
    if float(lon.max()) <= 180:
        return da

    return da.assign_coords({x_dim: ((lon + 180) % 360) - 180}).sortby(x_dim)


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

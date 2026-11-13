from __future__ import annotations

import numpy as np
import pytest
from affine import Affine
from pyproj import CRS

xr = pytest.importorskip("xarray")

from lonboard.layer._raster_xarray import (  # noqa: E402
    chunk_tile_size,
    coordinate_transform,
    default_min_zoom,
    find_crs,
    level_for,
    roll_longitude,
    spatial_dims,
    wgs84_bounds,
)
from lonboard.raster import AffineLevel  # noqa: E402


def _da(  # noqa: PLR0913
    lat,
    lon,
    *,
    dims=("lat", "lon"),
    attrs=None,
    lat_attrs=None,
    lon_attrs=None,
):
    data = np.zeros((len(lat), len(lon)), dtype="f4")
    da = xr.DataArray(
        data,
        coords={dims[0]: lat, dims[1]: lon},
        dims=dims,
        attrs=attrs or {},
    )
    if lat_attrs:
        da[dims[0]].attrs.update(lat_attrs)
    if lon_attrs:
        da[dims[1]].attrs.update(lon_attrs)
    return da


def test_spatial_dims_are_last_two():
    da = xr.DataArray(np.zeros((3, 4, 5)), dims=("band", "y", "x"))
    assert spatial_dims(da) == ("y", "x")


def test_spatial_dims_rejects_four_dims():
    da = xr.DataArray(np.zeros((2, 3, 4, 5)), dims=("time", "band", "y", "x"))
    with pytest.raises(ValueError, match=r"\.isel\(\)"):
        spatial_dims(da)


def test_coordinate_transform_north_up():
    da = _da(np.linspace(89.5, -89.5, 180), np.linspace(-179.5, 179.5, 360))
    assert coordinate_transform(da, "lat", "lon") == Affine(
        1.0,
        0.0,
        -180.0,
        0.0,
        -1.0,
        90.0,
    )


def test_coordinate_transform_south_up_and_descending_x():
    da = _da(np.array([0.5, 1.5, 2.5]), np.array([2.5, 1.5, 0.5]))
    assert coordinate_transform(da, "lat", "lon") == Affine(
        -1.0,
        0.0,
        3.0,
        0.0,
        1.0,
        0.0,
    )


def test_coordinate_transform_rejects_irregular():
    da = _da(np.array([0.0, 1.0, 3.0]), np.array([0.0, 1.0, 2.0]))
    with pytest.raises(ValueError, match="'lat' is not evenly spaced"):
        coordinate_transform(da, "lat", "lon")


def test_coordinate_transform_rejects_missing_coordinate():
    da = xr.DataArray(np.zeros((2, 2)), dims=("y", "x"))
    with pytest.raises(ValueError, match="'y'"):
        coordinate_transform(da, "y", "x")


def test_find_crs_geozarr_code():
    da = _da([1.0, 0.0], [0.0, 1.0], dims=("y", "x"), attrs={"proj:code": "EPSG:32612"})
    assert find_crs(da).to_epsg() == 32612


def test_find_crs_geozarr_projjson():
    da = _da(
        [1.0, 0.0],
        [0.0, 1.0],
        dims=("y", "x"),
        attrs={"proj:projjson": CRS.from_epsg(3857).to_json_dict()},
    )
    assert find_crs(da).to_epsg() == 3857


def test_find_crs_geographic_names():
    da = _da([1.0, 0.0], [0.0, 1.0], dims=("latitude", "longitude"))
    assert find_crs(da).to_epsg() == 4326


def test_find_crs_geographic_units():
    da = _da(
        [1.0, 0.0],
        [0.0, 1.0],
        dims=("y", "x"),
        lat_attrs={"units": "degrees_north"},
        lon_attrs={"units": "degrees_east"},
    )
    assert find_crs(da).to_epsg() == 4326


def test_find_crs_no_hit():
    with pytest.raises(ValueError, match="crs="):
        find_crs(_da([1.0, 0.0], [0.0, 1.0], dims=("y", "x")))


def test_roll_longitude():
    da = _da(np.array([0.5, -0.5]), np.array([0.5, 90.5, 180.5, 270.5]))
    rolled = roll_longitude(da, "lon")
    assert rolled["lon"].values.tolist() == [-179.5, -89.5, 0.5, 90.5]


def test_roll_longitude_noop():
    da = _da(np.array([0.5, -0.5]), np.array([-90.0, 0.0, 90.0]))
    assert roll_longitude(da, "lon") is da


def test_tile_size_explicit():
    assert chunk_tile_size(_da([1.0, 0.0], [0.0, 1.0]), "lat", "lon", 1024) == (
        1024,
        1024,
    )


def test_tile_size_without_chunks():
    assert chunk_tile_size(_da([1.0, 0.0], [0.0, 1.0]), "lat", "lon", None) == (
        512,
        512,
    )


def test_tile_size_from_dask_chunks():
    dask = pytest.importorskip("dask.array")
    da = xr.DataArray(dask.zeros((400, 600), chunks=(300, 128)), dims=("y", "x"))
    assert chunk_tile_size(da, "y", "x", None) == (256, 300)


def test_tile_size_irregular_dask_chunks_fall_back():
    dask = pytest.importorskip("dask.array")
    da = xr.DataArray(
        dask.zeros((400, 600), chunks=((100, 300), (600,))),
        dims=("y", "x"),
    )
    # Irregular y chunks fall back to 512; the single regular x chunk is kept.
    assert chunk_tile_size(da, "y", "x", None) == (600, 512)


def test_tile_size_from_zarr_store_chunks():
    zarr = pytest.importorskip("zarr")
    store = zarr.storage.MemoryStore()
    ds = xr.Dataset({"v": (("y", "x"), np.zeros((8, 8), "f4"))})
    ds.to_zarr(store, encoding={"v": {"chunks": (4, 8)}})
    lazy = xr.open_zarr(store, chunks=None)["v"]
    # 8 px chunks become 256 px tiles (32 chunks); 4 px chunks likewise
    assert chunk_tile_size(lazy, "y", "x", None) == (256, 256)


def test_tile_size_oversized_chunk_falls_back():
    dask = pytest.importorskip("dask.array")
    da = xr.DataArray(dask.zeros((4000, 4000), chunks=(4000, 512)), dims=("y", "x"))
    assert chunk_tile_size(da, "y", "x", None) == (512, 512)


def test_level_for_sizes():
    da = _da(np.linspace(89.5, -89.5, 180), np.linspace(-179.5, 179.5, 360))
    level = level_for(da, "lat", "lon", Affine(1, 0, -180, 0, -1, 90), (512, 256))
    assert (level.width, level.height, level.tile_width, level.tile_height) == (
        360,
        180,
        512,
        256,
    )


def test_wgs84_bounds_projected():
    level = AffineLevel(
        Affine(10.0, 0.0, 300000.0, 0.0, -10.0, 4100040.0),
        10980,
        10980,
        512,
        512,
    )
    b = wgs84_bounds(level, CRS.from_epsg(32612))
    assert b.minx == pytest.approx(-113.2, abs=0.2)
    assert b.maxy == pytest.approx(37.05, abs=0.1)


def test_default_min_zoom_small_global_array_is_zero():
    level = AffineLevel(Affine(1, 0, -180, 0, -1, 90), 360, 180, 512, 512)
    assert default_min_zoom(level, 111319.49, 0.0) == 0


def test_default_min_zoom_large_array():
    # 10 m pixels: a 512 px tile is 5120 m; a quarter of that on screen is
    # 40 m per CSS pixel, which is zoom ceil(log2(156543.03 / 40)) = 12 at the
    # equator.
    level = AffineLevel(
        Affine(10.0, 0.0, 0.0, 0.0, -10.0, 0.0),
        100000,
        100000,
        512,
        512,
    )
    assert default_min_zoom(level, 1.0, 0.0) == 12

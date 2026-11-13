from __future__ import annotations

import numpy as np
import pytest
from affine import Affine
from pyproj import CRS

xr = pytest.importorskip("xarray")

from lonboard.layer._raster_xarray import (  # noqa: E402
    coordinate_transform,
    find_crs,
    roll_longitude,
    spatial_dims,
)


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

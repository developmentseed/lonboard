from __future__ import annotations

import geodatasets
import numpy as np
import pyarrow as pa
import pytest
from pyogrio.raw import read_arrow
from traitlets import TraitError

from lonboard import (
    BitmapLayer,
    Map,
    PointCloudLayer,
    ScatterplotLayer,
    SolidPolygonLayer,
    viz,
)
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard.layer_extension import DataFilterExtension

from . import compat


def test_accessor_length_validation():
    """Accessor length must match table length"""
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([1, 2], [3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)

    with pytest.raises(TraitError, match="same length as table"):
        _layer = ScatterplotLayer.from_geopandas(gdf, get_radius=np.array([1]))

    with pytest.raises(TraitError, match="same length as table"):
        _layer = ScatterplotLayer.from_geopandas(gdf, get_radius=np.array([1, 2, 3]))

    _layer = ScatterplotLayer.from_geopandas(gdf, get_radius=np.array([1, 2]))


def test_accessor_length_validation_extension():
    """Accessor length must match table length"""
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([1, 2], [3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)
    extension = DataFilterExtension()

    with pytest.raises(TraitError, match="same length as table"):
        _layer = ScatterplotLayer.from_geopandas(
            gdf, extensions=[extension], get_filter_value=np.array([1])
        )

    with pytest.raises(TraitError, match="same length as table"):
        _layer = ScatterplotLayer.from_geopandas(
            gdf, extensions=[extension], get_filter_value=np.array([1, 2, 3])
        )

    _layer = ScatterplotLayer.from_geopandas(
        gdf, extensions=[extension], get_radius=np.array([1, 2])
    )


def test_layer_fails_with_unexpected_argument():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([1, 2], [3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)

    with pytest.raises(TypeError, match="Unexpected keyword argument"):
        _layer = ScatterplotLayer.from_geopandas(gdf, unknown_keyword="foo")


def test_layer_outside_4326_range():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    # Table outside of epsg:4326 range
    points = shapely.points([1000000, 2000000], [3000000, 4000000])
    gdf = gpd.GeoDataFrame(geometry=points)

    with pytest.raises(ValueError, match="outside of WGS84 bounds"):
        _layer = ScatterplotLayer.from_geopandas(gdf)


def test_layer_from_geoarrow_pyarrow():
    gpd = pytest.importorskip("geopandas")
    ga = pytest.importorskip("geoarrow.pyarrow")
    shapely = pytest.importorskip("shapely")

    points = gpd.GeoSeries(shapely.points([1, 2], [3, 4]))

    # convert to geoarrow.pyarrow Table (currently requires to ensure interleaved
    # coordinates manually)
    points = ga.with_coord_type(ga.as_geoarrow(points), ga.CoordType.INTERLEAVED)
    table = pa.table({"geometry": points})

    _layer = ScatterplotLayer(table=table)


@pytest.mark.skipif(not compat.HAS_SHAPELY, reason="shapely not available")
def test_layer_wkb_geoarrow():
    path = geodatasets.get_path("naturalearth.land")
    meta, table = read_arrow(path)
    _layer = SolidPolygonLayer(table=table)


@pytest.mark.skipif(not compat.HAS_SHAPELY, reason="shapely not available")
def test_layer_wkb_geoarrow_wrong_geom_type():
    path = geodatasets.get_path("naturalearth.land")
    meta, table = read_arrow(path)
    # Use regex as set will have unknown ordering between multipoint and point
    with pytest.raises(
        TraitError,
        match=r"Expected one of geoarrow\..*point, geoarrow\..*point geometry types",
    ):
        _layer = ScatterplotLayer(table=table)


def test_warning_no_crs_shapely():
    shapely = pytest.importorskip("shapely")

    points = shapely.points([0, 1, 2], [2, 3, 4])
    with pytest.warns(match="No CRS exists on data"):
        _ = viz(points)


def test_warning_no_crs_geopandas():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([0, 1, 2], [2, 3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)
    with pytest.warns(match="No CRS exists on data"):
        _ = viz(gdf)


def test_warning_no_crs_arrow():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([0, 1, 2], [2, 3, 4])
    gdf = gpd.GeoDataFrame(geometry=points)
    table = geopandas_to_geoarrow(gdf)
    with pytest.warns(match="No CRS exists on data"):
        _ = viz(table)


# Test layer types
def test_bitmap_layer():
    layer = BitmapLayer(
        image="https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/sf-districts.png",
        bounds=[-122.5190, 37.7045, -122.355, 37.829],
    )
    _m = Map(layer)


def test_point_cloud_layer():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    points = shapely.points([0, 1], [2, 3], [4, 5])
    gdf = gpd.GeoDataFrame(geometry=points)
    _layer = PointCloudLayer.from_geopandas(gdf)

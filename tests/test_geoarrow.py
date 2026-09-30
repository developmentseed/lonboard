import json
from tempfile import NamedTemporaryFile

import geodatasets
import geopandas as gpd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import shapely
from arro3.core import ChunkedArray, Table
from geoarrow.rust.core import GeoArray, geometry, points
from pyproj import CRS
from traitlets import TraitError

from lonboard import ScatterplotLayer, SolidPolygonLayer, viz
from lonboard._constants import OGC_84
from lonboard._geoarrow.geopandas_interop import geopandas_to_geoarrow
from lonboard._geoarrow.ops.reproject import reproject_table
from lonboard._geoarrow.utils import check_float_coords
from lonboard._utils import get_geometry_column_index


def test_geopandas_table_reprojection():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    layer = SolidPolygonLayer.from_geopandas(gdf)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"],
    )["crs"]
    assert (
        CRS.from_json(
            reprojected_crs_str,
        )
        == OGC_84
    ), "layer should be reprojected to WGS84"


def test_geoarrow_table_reprojection():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    table = geopandas_to_geoarrow(gdf)

    geom_col_idx = get_geometry_column_index(table.schema)
    assert geom_col_idx is not None, "geom column should exist"

    geom_field = table.schema.field(geom_col_idx)
    assert b"ARROW:extension:metadata" in geom_field.metadata, (
        "Metadata key should exist"
    )

    crs_dict = json.loads(geom_field.metadata[b"ARROW:extension:metadata"])["crs"]
    assert gdf.crs == CRS.from_json_dict(
        crs_dict,
    ), "round trip crs should match gdf crs"

    layer = SolidPolygonLayer(table)

    layer_geom_col_idx = get_geometry_column_index(layer.table.schema)
    layer_geom_field = layer.table.schema.field(layer_geom_col_idx)

    reprojected_crs_str = json.loads(
        layer_geom_field.metadata[b"ARROW:extension:metadata"],
    )["crs"]
    assert (
        CRS.from_json(
            reprojected_crs_str,
        )
        == OGC_84
    ), "layer should be reprojected to WGS84"


def test_reproject_sliced_array():
    """See https://github.com/developmentseed/lonboard/issues/390"""
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))
    table = geopandas_to_geoarrow(gdf)
    sliced_table = Table.from_arrow(pa.table(table).slice(2))
    # This should work even with a sliced array.
    _reprojected = reproject_table(sliced_table, to_crs=OGC_84)


def test_geoparquet_metadata():
    gpd = pytest.importorskip("geopandas")

    gdf = gpd.read_file(geodatasets.get_path("nybb"))

    with NamedTemporaryFile("+wb", suffix=".parquet") as f:
        gdf.to_parquet(f)
        table = pq.read_table(f)

    _layer = SolidPolygonLayer(table)


def test_read_geometry_type():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    arr = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb"))
    geometry_arr = arr.cast(geometry())

    # Pass to viz
    out = viz(geometry_arr)
    assert isinstance(out.layers[0], ScatterplotLayer)

    # Pass to layer directly
    _layer = ScatterplotLayer(geometry_arr)


def test_mixed_point_multipoint_types_layer_constructor():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    geometry_arr1 = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb")).cast(
        geometry(),
    )

    multipoints = shapely.multipoints([[1, 2], [3, 4], [5, 6]])
    geometry_arr2 = GeoArray.from_arrow(
        gpd.GeoSeries(multipoints).to_arrow("wkb"),
    ).cast(geometry())

    ca = ChunkedArray([geometry_arr1, geometry_arr2])

    # Pass to viz
    out = viz(ca)
    assert isinstance(out.layers[0], ScatterplotLayer)
    assert len(out.layers) == 1

    # Pass to layer directly
    _layer = ScatterplotLayer(ca)


def test_read_geometry_type_from_table():
    points = shapely.points([1, 2, 3], [4, 5, 6])
    arr = GeoArray.from_arrow(gpd.GeoSeries(points).to_arrow("wkb"))
    geometry_arr = arr.cast(geometry())
    table = Table.from_arrays([geometry_arr], names=["geometry"])

    # Pass to viz
    out = viz(table)
    assert isinstance(out.layers[0], ScatterplotLayer)

    # Pass to layer directly
    _layer = ScatterplotLayer(table)


def test_geoarrow_geometry_with_crs():
    coords = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float64)

    crs = "EPSG:4326"
    geometry_array = points(coords, crs=crs).cast(geometry(crs=crs))
    m = viz(geometry_array)
    assert isinstance(m.layers[0], ScatterplotLayer)


def test_geoarrow_string_view_column():
    # Note: this test is really for the _JavaScript_ side to ensure the Wasm code can
    # load a Parquet file with a string view column. We don't have a headless setup in
    # CI, but you can run this test manually and ensure it renders.
    coords = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float64)
    geometry_array = points(coords)

    string_col = pa.array(["a", "b", "c"], type=pa.string_view())
    table = Table.from_arrays(
        [geometry_array, string_col],
        names=["geometry", "string_view"],
    )

    m = viz(table)
    assert isinstance(m.layers[0], ScatterplotLayer)


# Number of lists around the coordinates of each native GeoArrow geometry type
COORD_NESTING = {
    "point": 0,
    "linestring": 1,
    "multipoint": 1,
    "polygon": 2,
    "multilinestring": 2,
    "multipolygon": 3,
}


def native_geometry_table(
    geom_type: str,
    coord_type: pa.DataType,
    *,
    interleaved: bool,
) -> pa.Table:
    """Make a table of native GeoArrow geometries with the given coordinate type."""
    # A closed ring, so that the coordinates are valid for every geometry type
    if interleaved:
        xy = pa.array([0, 0, 1, 0, 1, 1, 0, 0], coord_type)
        geometry = pa.FixedSizeListArray.from_arrays(xy, 2)
    else:
        x = pa.array([0, 1, 1, 0], coord_type)
        y = pa.array([0, 0, 1, 0], coord_type)
        geometry = pa.StructArray.from_arrays([x, y], names=["x", "y"])

    for _ in range(COORD_NESTING[geom_type]):
        geometry = pa.ListArray.from_arrays([0, len(geometry)], geometry)

    field = pa.field(
        "geometry",
        geometry.type,
        metadata={"ARROW:extension:name": f"geoarrow.{geom_type}"},
    )
    return pa.Table.from_arrays([geometry], schema=pa.schema([field]))


@pytest.mark.parametrize("geom_type", list(COORD_NESTING))
@pytest.mark.parametrize("interleaved", [True, False])
def test_viz_integer_coords_raise(geom_type: str, *, interleaved: bool):
    """See https://github.com/developmentseed/lonboard/issues/608"""
    table = native_geometry_table(geom_type, pa.int64(), interleaved=interleaved)

    with pytest.raises(ValueError, match=r"must be floating point, got .*Int64"):
        viz(table)


@pytest.mark.parametrize(
    ("layer_cls", "geom_type"),
    [(ScatterplotLayer, "point"), (SolidPolygonLayer, "multipolygon")],
)
@pytest.mark.parametrize("interleaved", [True, False])
def test_layer_integer_coords_raise(layer_cls, geom_type: str, *, interleaved: bool):
    table = native_geometry_table(geom_type, pa.int32(), interleaved=interleaved)

    with pytest.raises(ValueError, match=r"must be floating point, got .*Int32"):
        layer_cls(table)


def test_viz_integer_box_coords_raise():
    names = ["xmin", "ymin", "xmax", "ymax"]
    boxes = pa.StructArray.from_arrays(
        [pa.array([value], pa.int64()) for value in [0, 0, 1, 1]],
        names=names,
    )
    field = pa.field(
        "geometry",
        boxes.type,
        metadata={"ARROW:extension:name": "geoarrow.box"},
    )
    table = pa.Table.from_arrays([boxes], schema=pa.schema([field]))

    with pytest.raises(ValueError, match=r"must be floating point, got .*Int64"):
        viz(table)


def test_assigning_table_integer_coords_raises():
    layer = ScatterplotLayer(
        native_geometry_table("point", pa.float64(), interleaved=True),
    )
    table = native_geometry_table("point", pa.int64(), interleaved=True)

    with pytest.raises(TraitError, match=r"must be floating point, got .*Int64"):
        layer.table = Table.from_arrow(table)


@pytest.mark.parametrize("geom_type", list(COORD_NESTING))
@pytest.mark.parametrize("interleaved", [True, False])
def test_viz_float64_coords_accepted(geom_type: str, *, interleaved: bool):
    table = native_geometry_table(geom_type, pa.float64(), interleaved=interleaved)

    m = viz(table)

    assert m.layers[0].table.num_rows == table.num_rows


@pytest.mark.parametrize("geom_type", list(COORD_NESTING))
@pytest.mark.parametrize("interleaved", [True, False])
def test_float32_coords_pass_check(geom_type: str, *, interleaved: bool):
    # Only the check is tested: a layer can't always convert or serialize float32
    # coordinates
    table = native_geometry_table(geom_type, pa.float32(), interleaved=interleaved)

    check_float_coords(Table.from_arrow(table))

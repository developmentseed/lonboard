"""Layers and `viz` given empty record batches, empty geometries, or no rows.

See https://github.com/developmentseed/lonboard/issues/892 and
https://github.com/developmentseed/lonboard/issues/146
"""

from __future__ import annotations

import geoarrow.pyarrow as gap
import pyarrow as pa
import pytest
from arro3.core import Table

from lonboard import ScatterplotLayer, SolidPolygonLayer, viz


def wkb_reader(*batches: list[str]) -> pa.RecordBatchReader:
    """Make a stream of WKB record batches, one per (possibly empty) list of WKT."""
    record_batches = [
        pa.record_batch(
            {
                "geometry": gap.with_crs(
                    gap.as_wkb(pa.array(wkt, pa.string())),
                    "OGC:CRS84",
                ),
            },
        )
        for wkt in batches
    ]
    schema = pa.schema(
        [pa.field("geometry", gap.wkb().with_crs("OGC:CRS84"))],
    )
    return pa.RecordBatchReader.from_batches(schema, record_batches)


def view_center(m) -> tuple[float, float, float]:
    return (m.view_state.longitude, m.view_state.latitude, m.view_state.zoom)


@pytest.mark.parametrize(
    "wkt",
    [
        "POINT (10 20)",
        "LINESTRING (0 0, 20 40)",
        "POLYGON ((0 0, 20 0, 20 40, 0 40, 0 0))",
    ],
)
@pytest.mark.parametrize("empty_first", [False, True])
def test_viz_skips_empty_record_batches(wkt: str, *, empty_first: bool):
    batches = [[], [wkt]] if empty_first else [[wkt], []]
    m = viz(wkb_reader(*batches))

    layer = m.layers[0]
    assert layer.table.num_rows == 1
    # Serializing the table for the frontend must not see a 0-row batch
    layer.get_state()


def test_layer_skips_empty_record_batches():
    pts = gap.with_crs(gap.as_geoarrow(["POINT (0 0)", "POINT (10 10)"]), "OGC:CRS84")
    table = pa.Table.from_batches(
        [
            pa.record_batch({"geometry": pts.slice(0, 1)}),
            pa.record_batch({"geometry": pts.slice(0, 0)}),
            pa.record_batch({"geometry": pts.slice(1, 1)}),
        ],
    )

    layer = ScatterplotLayer(table, _rows_per_chunk=1)

    assert [batch.num_rows for batch in layer.table.to_batches()] == [1, 1]
    layer.get_state()


def test_assigning_table_skips_empty_record_batches():
    pts = gap.with_crs(gap.as_geoarrow(["POINT (0 0)", "POINT (10 10)"]), "OGC:CRS84")
    layer = ScatterplotLayer(pa.table({"geometry": pts}))

    [batch] = layer.table.to_batches()
    layer.table = Table.from_batches(
        [batch.slice(0, 1), batch.slice(0, 0)],
        schema=layer.table.schema,
    )

    assert [batch.num_rows for batch in layer.table.to_batches()] == [1]
    layer.get_state()


def test_view_state_ignores_empty_points():
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    gdf = gpd.GeoDataFrame(
        geometry=[shapely.Point(0, 0), shapely.Point(10, 10), shapely.Point()],
        crs="EPSG:4326",
    )
    m = viz(gdf)

    longitude, latitude, zoom = view_center(m)
    assert longitude == pytest.approx(5)
    assert latitude == pytest.approx(5)
    assert zoom > 0


@pytest.mark.parametrize(
    "geom_type",
    [
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    ],
)
@pytest.mark.parametrize("crs", ["EPSG:4326", "EPSG:3857"])
def test_view_state_defaults_when_all_geometries_empty(geom_type: str, crs: str):
    gpd = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely")

    empty = getattr(shapely, geom_type)()
    gdf = gpd.GeoDataFrame(geometry=[empty, empty], crs=crs)
    m = viz(gdf)

    assert m.layers[0].table.num_rows == 2
    assert view_center(m) == (0, 0, 0)


def test_layer_all_empty_polygons_separated_coords():
    # geoarrow-pyarrow can't infer a type from all-empty input
    polygon_type = gap.polygon().with_coord_type(gap.CoordType.SEPARATED)
    polygons = gap.with_crs(
        gap.as_geoarrow(["POLYGON EMPTY", "POLYGON EMPTY"], type=polygon_type),
        "OGC:CRS84",
    )
    table = pa.table({"geometry": polygons})

    layer = SolidPolygonLayer(table)

    assert layer.table.num_rows == 2
    layer.get_state()


@pytest.mark.parametrize(
    "batches",
    [[], [[]], [[], []]],
    ids=["no-batches", "one-empty", "two-empty"],
)
def test_viz_with_no_rows_raises(batches: list[list[str]]):
    with pytest.raises(ValueError, match="no rows"):
        viz(wkb_reader(*batches))


def test_layer_with_no_rows_raises():
    pts = gap.with_crs(gap.as_geoarrow(["POINT (0 0)"]), "OGC:CRS84")
    table = pa.Table.from_batches([pa.record_batch({"geometry": pts.slice(0, 0)})])

    with pytest.raises(ValueError, match="no rows"):
        ScatterplotLayer(table)

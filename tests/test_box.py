import geoarrow.pyarrow as ga
from arro3.core import ChunkedArray, Table

from lonboard import Map, PolygonLayer, SolidPolygonLayer, viz


def test_viz_box():
    arr = ga.box(
        [
            "LINESTRING (0 10, 34 -1)",
            "LINESTRING (10 20, 44 -10)",
            "LINESTRING (20 40, 54 5)",
        ],
    )

    m = viz(arr)
    assert isinstance(m.layers[0], PolygonLayer)


def test_box_polygon_layer():
    arr = ga.box(
        [
            "LINESTRING (0 10, 34 -1)",
            "LINESTRING (10 20, 44 -10)",
            "LINESTRING (20 40, 54 5)",
        ],
    )
    layer = PolygonLayer(arr)
    _m = Map(layer)


def test_box_polygon_layer_chunked_array():
    arr = ga.box(
        [
            "LINESTRING (0 10, 34 -1)",
            "LINESTRING (10 20, 44 -10)",
            "LINESTRING (20 40, 54 5)",
        ],
    )
    ca = ChunkedArray([arr])
    layer = PolygonLayer(ca)
    _m = Map(layer)


def test_viz_box_polygon_layer():
    arr = ga.box(
        [
            "LINESTRING (0 10, 34 -1)",
            "LINESTRING (10 20, 44 -10)",
            "LINESTRING (20 40, 54 5)",
        ],
    )
    table = Table.from_arrays([arr], names=["geometry"])  # type: ignore
    assert (
        table.field("geometry").metadata_str["ARROW:extension:name"] == "geoarrow.box"
    )

    layer = PolygonLayer(table=table)
    assert (
        layer.table.field("geometry").metadata_str["ARROW:extension:name"]
        == "geoarrow.polygon"
    )

    layer2 = SolidPolygonLayer(table=table)
    assert (
        layer2.table.field("geometry").metadata_str["ARROW:extension:name"]
        == "geoarrow.polygon"
    )

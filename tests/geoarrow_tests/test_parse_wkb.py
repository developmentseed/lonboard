from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING, Literal

import pytest
import shapely
from arro3.core import Array, DataType, Field, Schema, Table

from lonboard import PolygonLayer, ScatterplotLayer, viz
from lonboard._constants import EXTENSION_NAME
from lonboard._geoarrow.parse_wkb import parse_serialized_table

if TYPE_CHECKING:
    from numpy.typing import NDArray


@pytest.mark.parametrize(
    ("serialization", "view_type"),
    list(product(["wkb", "wkt"], [True, False])),
)
def test_parse_wkb(
    serialization: Literal["wkb", "wkt"],
    view_type: bool,  # noqa: FBT001
):
    points = shapely.points([1, 2, 3], [4, 5, 6])
    if serialization == "wkb":
        serialized_np_arr: NDArray = shapely.to_wkb(points)
        geoarrow_type = "geoarrow.wkb"
    else:
        serialized_np_arr = shapely.to_wkt(points)
        geoarrow_type = "geoarrow.wkt"

    if serialization == "wkb":
        dtype = DataType.binary_view() if view_type else DataType.binary()
    else:
        dtype = DataType.string_view() if view_type else DataType.string()

    arr = Array(list(serialized_np_arr), type=dtype)
    schema = Schema(
        [
            Field(
                "geometry",
                arr.type,
                metadata={"ARROW:extension:name": geoarrow_type},
            ),
        ],
    )
    table = Table.from_arrays([arr], schema=schema)
    split_tables = parse_serialized_table(table)
    assert len(split_tables) == 1
    assert (
        split_tables[0].schema.field(0).metadata[b"ARROW:extension:name"]
        == EXTENSION_NAME.POINT
    )

    m = viz(table)
    assert isinstance(m.layers[0], ScatterplotLayer)


@pytest.mark.parametrize(
    ("serialization", "view_type"),
    list(product(["wkb", "wkt"], [True, False])),
)
def test_parse_mixed_wkb(
    serialization: Literal["wkb", "wkt"],
    view_type: bool,  # noqa: FBT001
):
    geoms = [
        shapely.geometry.Point(1, 4),
        shapely.geometry.LineString([(2, 5), (3, 6)]),
        shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
        shapely.geometry.MultiPoint([shapely.geometry.Point(1, 4)]),
        shapely.geometry.MultiLineString(
            [shapely.geometry.LineString([(2, 5), (3, 6)])],
        ),
        shapely.geometry.MultiPolygon(
            [
                shapely.geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
            ],
        ),
    ]

    if serialization == "wkb":
        serialized_np_arr: NDArray = shapely.to_wkb(geoms)
        geoarrow_type = "geoarrow.wkb"
    else:
        serialized_np_arr = shapely.to_wkt(geoms)
        geoarrow_type = "geoarrow.wkt"

    if serialization == "wkb":
        dtype = DataType.binary_view() if view_type else DataType.binary()
    else:
        dtype = DataType.string_view() if view_type else DataType.string()

    arr = Array(list(serialized_np_arr), type=dtype)
    schema = Schema(
        [
            Field(
                "geometry",
                arr.type,
                metadata={"ARROW:extension:name": geoarrow_type},
            ),
        ],
    )
    table = Table.from_arrays([arr], schema=schema)
    split_tables = parse_serialized_table(table)
    assert len(split_tables) == 6
    assert (
        split_tables[0].schema.field(0).metadata[b"ARROW:extension:name"]
        == EXTENSION_NAME.MULTIPOLYGON
    )

    m = viz(table)
    assert isinstance(m.layers[0], PolygonLayer)

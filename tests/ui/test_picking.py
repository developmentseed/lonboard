"""Clicking a feature sets `selected_index`, for each geometry layer type."""

import geopandas as gpd
import h3
import pandas as pd
import pytest
from shapely.geometry import LineString, MultiPolygon, Point, box
from test_utils import TestConstants, setup_map_widget

from lonboard import (
    H3HexagonLayer,
    Map,
    PathLayer,
    PolygonLayer,
    ScatterplotLayer,
    SolidPolygonLayer,
)
from lonboard.layer import BaseArrowLayer

LAYER_TYPES = ["ScatterplotLayer", "PathLayer", "PolygonLayer", "SolidPolygonLayer"]

# The map is centered on (0, 0). Only the last row has a feature there, so a click
# on the center should select row 2.
LONGITUDES = [-40, 40, 0]

# Longitudes of features that are away from the center of the map.
OTHER_LONGITUDES = [-60, -40, -20, 20, 40]


def longitudes_with_center_at(row: int, *, num_rows: int) -> list[int]:
    """Longitudes of `num_rows` features where only `row` is at the map center."""
    longitudes = OTHER_LONGITUDES[: num_rows - 1]
    longitudes.insert(row, 0)
    return longitudes


def make_layer(
    layer_type: str,
    longitudes: list[int],
    *,
    rows_per_chunk: int | None = None,
) -> BaseArrowLayer:
    if layer_type == "ScatterplotLayer":
        geoms = [Point(lon, 0) for lon in longitudes]
        return ScatterplotLayer.from_geopandas(
            gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326"),
            radius_min_pixels=20,
            _rows_per_chunk=rows_per_chunk,
        )

    if layer_type == "PathLayer":
        geoms = [LineString([(lon - 5, 0), (lon + 5, 0)]) for lon in longitudes]
        return PathLayer.from_geopandas(
            gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326"),
            width_min_pixels=20,
            _rows_per_chunk=rows_per_chunk,
        )

    geoms = [box(lon - 5, -5, lon + 5, 5) for lon in longitudes]
    gdf = gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326")
    if layer_type == "PolygonLayer":
        return PolygonLayer.from_geopandas(gdf, _rows_per_chunk=rows_per_chunk)
    if layer_type == "SolidPolygonLayer":
        return SolidPolygonLayer.from_geopandas(gdf, _rows_per_chunk=rows_per_chunk)

    raise ValueError(f"Unexpected layer type {layer_type}")


def batch_lengths(layer: BaseArrowLayer) -> list[int]:
    return [batch.num_rows for batch in layer.table.to_batches()]


def wait_for_selected_index(page_session, layer: BaseArrowLayer) -> int | None:
    """Wait for a click in the browser to set `selected_index` in Python."""
    for _ in range(50):
        if layer.selected_index is not None:
            break
        page_session.wait_for_timeout(100)
    return layer.selected_index


def click_map(page_session, m: Map, *, offset_y: int = 0) -> None:
    """Click the center of the map, or `offset_y` pixels below it."""
    canvas = setup_map_widget(page_session, m)
    # Give the layer time to finish rendering before picking
    page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

    canvas_box = canvas.bounding_box()
    assert canvas_box is not None
    page_session.mouse.click(
        canvas_box["x"] + canvas_box["width"] / 2,
        canvas_box["y"] + canvas_box["height"] / 2 + offset_y,
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("layer_type", LAYER_TYPES)
def test_click_sets_selected_index(page_session, layer_type: str):
    layer = make_layer(layer_type, LONGITUDES)
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    click_map(page_session, m)

    assert wait_for_selected_index(page_session, layer) == 2


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("layer_type", LAYER_TYPES)
def test_click_first_row_sets_selected_index(page_session, layer_type: str):
    # Index 0 is falsy in JavaScript; it must not be taken for "nothing picked"
    layer = make_layer(layer_type, longitudes_with_center_at(0, num_rows=3))
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    click_map(page_session, m)

    assert wait_for_selected_index(page_session, layer) == 0


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("layer_type", LAYER_TYPES)
@pytest.mark.parametrize(
    "clicked_row",
    [
        pytest.param(2, id="first-row-of-second-batch"),
        pytest.param(3, id="last-row-of-second-batch"),
        pytest.param(5, id="last-row-of-third-batch"),
    ],
)
def test_click_in_later_batch_sets_table_index(
    page_session,
    layer_type: str,
    clicked_row: int,
):
    # Each record batch is rendered as its own deck.gl layer, but `selected_index`
    # is the position of the row in the whole table.
    layer = make_layer(
        layer_type,
        longitudes_with_center_at(clicked_row, num_rows=6),
        rows_per_chunk=2,
    )
    assert batch_lengths(layer) == [2, 2, 2]

    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    click_map(page_session, m)

    assert wait_for_selected_index(page_session, layer) == clicked_row


@pytest.mark.usefixtures("solara_test")
def test_click_multipolygon_in_later_batch_sets_table_index(page_session):
    # Each row has two polygons: one to the north and one on the equator.
    # `selected_index` counts rows, not polygons.
    clicked_row = 3
    longitudes = longitudes_with_center_at(clicked_row, num_rows=4)
    geoms = [
        MultiPolygon([box(lon - 5, 25, lon + 5, 35), box(lon - 5, -5, lon + 5, 5)])
        for lon in longitudes
    ]
    gdf = gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326")
    layer = SolidPolygonLayer.from_geopandas(gdf, _rows_per_chunk=2)
    assert batch_lengths(layer) == [2, 2]

    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    click_map(page_session, m)

    assert wait_for_selected_index(page_session, layer) == clicked_row


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "clicked_row",
    [
        pytest.param(0, id="first-row-of-first-batch"),
        pytest.param(2, id="first-row-of-second-batch"),
        pytest.param(3, id="last-row-of-second-batch"),
    ],
)
def test_click_h3_cell_sets_table_index(page_session, clicked_row: int):
    # The H3 layer has no geometry column; the cells come from an accessor that is
    # chunked in the same way as the table.
    longitudes = longitudes_with_center_at(clicked_row, num_rows=4)
    cells = [h3.latlng_to_cell(0, lon, 1) for lon in longitudes]
    assert len(set(cells)) == len(cells)

    df = pd.DataFrame({"h3": cells})
    layer = H3HexagonLayer.from_pandas(df, get_hexagon=df["h3"], _rows_per_chunk=2)
    assert batch_lengths(layer) == [2, 2]

    latitude, longitude = h3.cell_to_latlng(cells[clicked_row])
    m = Map(
        layer,
        view_state={"longitude": longitude, "latitude": latitude, "zoom": 3},
    )
    click_map(page_session, m)

    assert wait_for_selected_index(page_session, layer) == clicked_row


@pytest.mark.usefixtures("solara_test")
def test_click_on_empty_map_does_not_set_selected_index(page_session):
    layer = make_layer("ScatterplotLayer", longitudes_with_center_at(0, num_rows=3))
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    # All features are on the equator, so there is nothing below the center
    click_map(page_session, m, offset_y=150)

    assert wait_for_selected_index(page_session, layer) is None

"""Clicking a feature sets `selected_index`, for each geometry layer type."""

import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point, box
from test_utils import TestConstants, setup_map_widget

from lonboard import Map, PathLayer, PolygonLayer, ScatterplotLayer, SolidPolygonLayer
from lonboard.layer import BaseArrowLayer

# The map is centered on (0, 0). Only the last row has a feature there, so a click
# on the center should select row 2.
LONGITUDES = [-40, 40, 0]


def make_layer(layer_type: str) -> BaseArrowLayer:
    if layer_type == "ScatterplotLayer":
        geoms = [Point(lon, 0) for lon in LONGITUDES]
        return ScatterplotLayer.from_geopandas(
            gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326"),
            radius_min_pixels=20,
        )

    if layer_type == "PathLayer":
        geoms = [LineString([(lon - 5, 0), (lon + 5, 0)]) for lon in LONGITUDES]
        return PathLayer.from_geopandas(
            gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326"),
            width_min_pixels=20,
        )

    geoms = [box(lon - 5, -5, lon + 5, 5) for lon in LONGITUDES]
    gdf = gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326")
    if layer_type == "PolygonLayer":
        return PolygonLayer.from_geopandas(gdf)
    if layer_type == "SolidPolygonLayer":
        return SolidPolygonLayer.from_geopandas(gdf)

    raise ValueError(f"Unexpected layer type {layer_type}")


def wait_for_selected_index(page_session, layer: BaseArrowLayer) -> int | None:
    """Wait for a click in the browser to set `selected_index` in Python."""
    for _ in range(50):
        if layer.selected_index is not None:
            break
        page_session.wait_for_timeout(100)
    return layer.selected_index


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "layer_type",
    ["ScatterplotLayer", "PathLayer", "PolygonLayer", "SolidPolygonLayer"],
)
def test_click_sets_selected_index(page_session, layer_type: str):
    layer = make_layer(layer_type)
    m = Map(layer, view_state={"longitude": 0, "latitude": 0, "zoom": 3})
    canvas = setup_map_widget(page_session, m)
    # Give the layer time to finish rendering before picking
    page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

    canvas_box = canvas.bounding_box()
    assert canvas_box is not None
    page_session.mouse.click(
        canvas_box["x"] + canvas_box["width"] / 2,
        canvas_box["y"] + canvas_box["height"] / 2,
    )

    assert wait_for_selected_index(page_session, layer) == 2

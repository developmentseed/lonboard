"""Bounding box interaction tests for Lonboard UI."""

import re
import sys
from pathlib import Path

import geopandas as gpd
import pytest
from IPython.display import display
from shapely.geometry import Point

from lonboard import Map
from lonboard.layer import ScatterplotLayer

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_geodataframe():
    """Simple GeoDataFrame for testing."""
    return gpd.GeoDataFrame(
        {"name": ["test_point"], "value": [1]},
        geometry=[Point(0, 0)],
        crs="EPSG:4326",
    )


@pytest.fixture
def sample_layer(sample_geodataframe):
    """Scatterplot layer for testing."""
    return ScatterplotLayer.from_geopandas(
        sample_geodataframe,
        get_fill_color=[255, 0, 0],
        get_radius=5000,
    )


@pytest.fixture
def sample_map(sample_layer):
    """Lonboard map for testing."""
    return Map(sample_layer)


def validate_geographic_data(data_text: str | None):
    """Validate geographic data in format: 'Selected bounds: (minLon, minLat, maxLon, maxLat)'."""
    assert data_text, "Expected data text to not be None"
    assert "None" not in data_text, "Expected output to contain coordinates"
    assert "(0, 0, 0, 0)" not in data_text, "Expected output to not be zeros"

    data_match = re.search(
        r"Selected bounds: \(([-\deE.]+), ([-\deE.]+), ([-\deE.]+), ([-\deE.]+)\)",
        data_text,
    )
    assert data_match, f"Expected to find data pattern in: {data_text}"

    if data_match:
        min_lon, min_lat, max_lon, max_lat = map(float, data_match.groups())

        assert min_lon != 0, "Coordinates should not be zero"
        assert min_lat != 0, "Coordinates should not be zero"
        assert max_lon != 0, "Coordinates should not be zero"
        assert max_lat != 0, "Coordinates should not be zero"

        assert min_lon < max_lon, "Min values should be less than max values"
        assert min_lat < max_lat, "Min values should be less than max values"

        assert -180 <= min_lon <= 180, "Longitude should be in range [-180, 180]"
        assert -180 <= max_lon <= 180, "Longitude should be in range [-180, 180]"

        assert -90 <= min_lat <= 90, "Latitude should be in range [-90, 90]"
        assert -90 <= max_lat <= 90, "Latitude should be in range [-90, 90]"


def draw_on_canvas(page_session, start_pos, end_pos):
    """Draw on canvas using canvas-relative coordinates."""
    canvas = page_session.locator("canvas").first

    canvas.click(position=start_pos)
    page_session.wait_for_timeout(300)
    canvas.hover(position=end_pos)
    page_session.wait_for_timeout(300)
    canvas.click(position=end_pos)
    page_session.wait_for_timeout(500)


@pytest.mark.usefixtures("solara_test")
def test_bbox_interaction_workflow(page_session, sample_map):
    """Test complete bounding box interaction workflow."""
    # Verify widget creation
    assert sample_map is not None
    assert hasattr(sample_map, "_model_name")
    assert sample_map._model_name == "AnyModel"

    # Display and wait for widget to render
    display(sample_map)
    canvas = page_session.locator("canvas").first
    canvas.wait_for(timeout=30000)

    # Verify UI components are present
    bbox_button = page_session.locator('button[aria-label*="Select"]')
    assert canvas.count() > 0, "Widget canvas should be present"
    assert bbox_button.count() > 0, "BBox button should be present"

    # Start bbox interaction
    bbox_button.wait_for(timeout=10000)
    bbox_button.click()

    # Verify interaction mode is active
    active_button = page_session.locator('button[aria-label*="Cancel"]')
    active_button.wait_for(timeout=5000)

    # Perform bbox selection using canvas-relative coordinates
    start_pos = {"x": 25, "y": 25}
    end_pos = {"x": 75, "y": 75}
    draw_on_canvas(page_session, start_pos, end_pos)

    # Verify bbox coordinates changed and are valid
    interaction_result = sample_map.selected_bounds
    assert interaction_result is not None, (
        "Expected bbox selected_bounds to be available after interaction"
    )

    # Validate the coordinates are proper geographic bounds
    bounds_string = f"Selected bounds: ({interaction_result[0]}, {interaction_result[1]}, {interaction_result[2]}, {interaction_result[3]})"
    validate_geographic_data(bounds_string)

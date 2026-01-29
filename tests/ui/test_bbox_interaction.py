"""Bounding box interaction tests for Lonboard UI."""

import pytest
from IPython.display import display
from test_utils import (
    TestConstants,
    draw_bbox_on_canvas,
    start_bbox_selection,
    validate_geographic_data,
    wait_for_canvas,
)


@pytest.mark.usefixtures("solara_test")
def test_bbox_interaction_workflow(page_session, sample_map):
    """Test complete bounding box interaction workflow."""
    # Verify widget creation
    assert sample_map is not None
    assert hasattr(sample_map, "_model_name")
    assert sample_map._model_name == "AnyModel"

    # Display and wait for widget to render
    display(sample_map)
    canvas = wait_for_canvas(page_session)

    # Verify UI components are present
    bbox_button = page_session.locator('button[aria-label*="Select"]')
    assert canvas.count() > 0, "Widget canvas should be present"
    assert bbox_button.count() > 0, "BBox button should be present"

    # Start bbox interaction
    start_bbox_selection(page_session)

    # Verify interaction mode is active
    active_button = page_session.locator('button[aria-label*="Cancel"]')
    active_button.wait_for(timeout=TestConstants.TIMEOUT_BUTTON_STATE)

    # Perform bbox selection using canvas-relative coordinates
    draw_bbox_on_canvas(page_session)

    # Verify bbox coordinates changed and are valid
    interaction_result = sample_map.selected_bounds
    assert interaction_result is not None, (
        "Expected bbox selected_bounds to be available after interaction"
    )

    # Validate the coordinates are proper geographic bounds
    bounds_string = f"Selected bounds: ({interaction_result[0]}, {interaction_result[1]}, {interaction_result[2]}, {interaction_result[3]})"
    validate_geographic_data(bounds_string)

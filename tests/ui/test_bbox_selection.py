"""Bbox selection tests."""

import pytest
from test_utils import (
    TestConstants,
    draw_bbox_on_canvas,
    setup_map_widget,
    start_bbox_selection,
    validate_geographic_bounds,
    verify_bbox_cleared,
    wait_for_button,
)


@pytest.mark.usefixtures("solara_test")
class TestBboxSelectionWorkflow:
    """Test bbox selection workflow."""

    def test_complete_bbox_workflow(self, page_session, sample_map):
        setup_map_widget(page_session, sample_map)

        # Initial state
        select_button = wait_for_button(
            page_session,
            "select",
            TestConstants.TIMEOUT_BUTTON_CLICK,
        )
        assert select_button.count() > 0

        # Start selection
        start_bbox_selection(page_session)
        cancel_button = wait_for_button(page_session, "cancel")
        assert cancel_button.count() > 0

        # Complete selection
        draw_bbox_on_canvas(page_session)

        # Verify results
        bounds = sample_map.selected_bounds
        assert bounds is not None
        assert validate_geographic_bounds(bounds)

        # Final state
        clear_button = wait_for_button(page_session, "clear")
        assert clear_button.count() > 0

    def test_bbox_cancel_after_start_point(self, page_session, sample_map):
        canvas = setup_map_widget(page_session, sample_map)

        start_bbox_selection(page_session)
        cancel_button = wait_for_button(page_session, "cancel")
        assert cancel_button.count() > 0

        # Set start point
        canvas.click(position=TestConstants.CANVAS_START_POS)
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        # Cancel selection
        cancel_button.click()
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Verify reset to initial state
        select_button = wait_for_button(page_session, "select")
        assert select_button.count() > 0
        assert verify_bbox_cleared(sample_map)

    def test_bbox_clear_after_completion(self, page_session, sample_map):
        setup_map_widget(page_session, sample_map)

        start_bbox_selection(page_session)
        draw_bbox_on_canvas(page_session)

        # Verify completion
        assert sample_map.selected_bounds is not None
        assert validate_geographic_bounds(sample_map.selected_bounds)

        # Clear selection
        clear_button = wait_for_button(page_session, "clear")
        assert clear_button.count() > 0
        clear_button.click()
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Verify reset
        assert verify_bbox_cleared(sample_map)
        select_button = wait_for_button(page_session, "select")
        assert select_button.count() > 0

    def test_bbox_hover_updates(self, page_session, sample_map):
        canvas = setup_map_widget(page_session, sample_map)
        start_bbox_selection(page_session)

        # Set start point
        canvas.click(position=TestConstants.CANVAS_START_POS)
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        # Test hover updates
        canvas.hover(position={"x": 50, "y": 50})
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)
        canvas.hover(position=TestConstants.CANVAS_END_POS)
        page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)

        # Complete selection
        canvas.click(position=TestConstants.CANVAS_END_POS)
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Verify bounds
        bounds = sample_map.selected_bounds
        assert bounds is not None
        assert bounds[0] < bounds[2]
        assert bounds[1] < bounds[3]


@pytest.mark.usefixtures("solara_test")
class TestToolbarStates:
    """Test toolbar button states."""

    def test_button_state_transitions(self, page_session, sample_map):
        setup_map_widget(page_session, sample_map)

        # Initial state
        select_button = wait_for_button(
            page_session,
            "select",
            TestConstants.TIMEOUT_BUTTON_CLICK,
        )
        assert select_button.count() > 0

        # Selection mode
        start_bbox_selection(page_session)
        cancel_button = wait_for_button(page_session, "cancel")
        assert cancel_button.count() > 0

        # Completed state
        draw_bbox_on_canvas(page_session)
        clear_button = wait_for_button(page_session, "clear")
        assert clear_button.count() > 0

        # Reset state
        clear_button.click()
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)
        select_button = wait_for_button(page_session, "select")
        assert select_button.count() > 0

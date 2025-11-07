"""Feature highlighting tests."""

import pytest
from test_utils import (
    TestConstants,
    click_feature_position,
    setup_map_widget,
    start_bbox_selection,
    wait_for_button,
)


@pytest.mark.usefixtures("solara_test")
class TestFeatureHighlighting:
    """Test feature highlighting."""

    def test_feature_click_stability(self, page_session, sample_map_with_side_panel):
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Click center position (might hit a feature)
        click_feature_position(page_session, "center")
        assert canvas.count() > 0

    def test_empty_space_click(self, page_session, sample_map_with_side_panel):
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Click empty space
        click_feature_position(page_session, "empty")
        assert canvas.count() > 0

    def test_multiple_clicks_stability(self, page_session, sample_map_with_side_panel):
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Multiple rapid clicks
        for position in ["empty", "center", "empty", "start", "empty"]:
            click_feature_position(page_session, position)
            assert canvas.count() > 0
            page_session.wait_for_timeout(200)

    def test_feature_highlighting_with_bbox_mode(
        self,
        page_session,
        sample_map_with_side_panel,
    ):
        canvas = setup_map_widget(page_session, sample_map_with_side_panel)

        # Start bbox mode
        start_bbox_selection(page_session)
        cancel_button = wait_for_button(page_session, "cancel")
        assert cancel_button.count() > 0

        # Click feature while in bbox mode
        click_feature_position(page_session, "center")
        assert canvas.count() > 0

        # Cancel bbox mode
        cancel_button.click()
        page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

        # Verify return to normal
        select_button = wait_for_button(page_session, "select")
        assert select_button.count() > 0

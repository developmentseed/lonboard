"""Test utilities and constants."""

import re
from typing import ClassVar


class TestConstants:
    CANVAS_START_POS: ClassVar[dict[str, int]] = {"x": 25, "y": 25}
    CANVAS_END_POS: ClassVar[dict[str, int]] = {"x": 75, "y": 75}
    CANVAS_CENTER_POS: ClassVar[dict[str, int]] = {"x": 400, "y": 300}
    CANVAS_EMPTY_POS: ClassVar[dict[str, int]] = {"x": 100, "y": 100}
    TIMEOUT_WIDGET_LOAD = 30000
    TIMEOUT_BUTTON_CLICK = 10000
    TIMEOUT_BUTTON_STATE = 5000
    TIMEOUT_INTERACTION = 300
    TIMEOUT_AFTER_CLICK = 500


def validate_geographic_bounds(bounds):
    """Check if bounds are valid geographic coordinates."""
    if not bounds or len(bounds) != 4:
        return False

    min_lon, min_lat, max_lon, max_lat = bounds

    # Skip validation if all zeros (cleared state)
    if all(coord == 0 for coord in bounds):
        return True

    return (
        -180 <= min_lon <= 180
        and -180 <= max_lon <= 180
        and -90 <= min_lat <= 90
        and -90 <= max_lat <= 90
        and min_lon < max_lon
        and min_lat < max_lat
    )


def validate_geographic_data(data_text: str | None):
    """Validate geographic data string format."""
    assert data_text
    assert "None" not in data_text
    assert "(0, 0, 0, 0)" not in data_text

    data_match = re.search(
        r"Selected bounds: \(([-\deE.]+), ([-\deE.]+), ([-\deE.]+), ([-\deE.]+)\)",
        data_text,
    )
    assert data_match, f"Expected to find data pattern in: {data_text}"

    min_lon, min_lat, max_lon, max_lat = map(float, data_match.groups())
    assert all(coord != 0 for coord in (min_lon, min_lat, max_lon, max_lat))
    assert min_lon < max_lon
    assert min_lat < max_lat
    assert -180 <= min_lon <= 180
    assert -180 <= max_lon <= 180
    assert -90 <= min_lat <= 90
    assert -90 <= max_lat <= 90


def draw_bbox_on_canvas(page_session, start_pos=None, end_pos=None):
    """Draw bbox on canvas."""
    if start_pos is None:
        start_pos = TestConstants.CANVAS_START_POS
    if end_pos is None:
        end_pos = TestConstants.CANVAS_END_POS

    canvas = page_session.locator("canvas").first
    canvas.click(position=start_pos)
    page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)
    canvas.hover(position=end_pos)
    page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)
    canvas.click(position=end_pos)
    page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)


def start_bbox_selection(page_session):
    """Start bbox selection mode."""
    select_button = page_session.locator('button[aria-label*="Select"]')
    select_button.wait_for(timeout=TestConstants.TIMEOUT_BUTTON_CLICK)
    select_button.click()
    page_session.wait_for_timeout(TestConstants.TIMEOUT_INTERACTION)


def wait_for_canvas(page_session):
    """Wait for map canvas."""
    canvas = page_session.locator("canvas").first
    canvas.wait_for(timeout=TestConstants.TIMEOUT_WIDGET_LOAD)
    return canvas


def verify_bbox_cleared(sample_map):
    """Check if bbox selection is cleared."""
    bounds = sample_map.selected_bounds
    return bounds is None or all(x == 0 for x in bounds) if bounds else True


def get_button(page_session, button_type: str):
    """Get toolbar button by type."""
    button_selectors = {
        "select": 'button[aria-label*="Select"]',
        "cancel": 'button[aria-label*="Cancel"]',
        "clear": 'button[aria-label*="Clear"]',
    }

    if button_type not in button_selectors:
        raise ValueError(f"Unknown button type: {button_type}")

    return page_session.locator(button_selectors[button_type])


def wait_for_button(page_session, button_type: str, timeout=None):
    """Wait for toolbar button."""
    if timeout is None:
        timeout = TestConstants.TIMEOUT_BUTTON_STATE

    button = get_button(page_session, button_type)
    button.wait_for(timeout=timeout)
    return button


def setup_map_widget(page_session, sample_map):
    """Setup map widget for testing."""
    from IPython.display import display

    assert sample_map is not None
    assert hasattr(sample_map, "_model_name")
    assert sample_map._model_name == "AnyModel"

    display(sample_map)
    canvas = wait_for_canvas(page_session)
    assert canvas.count() > 0
    return canvas


def click_feature_position(page_session, position_type: str = "center"):
    """Click on predefined canvas position."""
    positions = {
        "center": TestConstants.CANVAS_CENTER_POS,
        "empty": TestConstants.CANVAS_EMPTY_POS,
        "start": TestConstants.CANVAS_START_POS,
        "end": TestConstants.CANVAS_END_POS,
    }

    if position_type not in positions:
        raise ValueError(f"Unknown position type: {position_type}")

    canvas = page_session.locator("canvas").first
    canvas.click(position=positions[position_type])
    page_session.wait_for_timeout(TestConstants.TIMEOUT_AFTER_CLICK)

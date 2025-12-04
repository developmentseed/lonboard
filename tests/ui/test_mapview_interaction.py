"""Mapview interaction tests."""

import pytest
from IPython.display import display

from lonboard import Map
from lonboard.view_state import MapViewState


@pytest.fixture
def sample_map():
    """Lonboard map for testing."""
    return Map([])


def click_and_drag_canvas(
    page_session,
    start_pos,
    end_pos,
    button,
):
    """Simulate click and drag on the map.

    Start and end positions are 0-100 percentages of the canvas size.
    """
    canvas = page_session.locator("canvas").first
    bbox = canvas.bounding_box()

    # Convert relative coords to absolute pixels
    start_x = bbox["x"] + (start_pos["x"] / 100) * bbox["width"]
    start_y = bbox["y"] + (start_pos["y"] / 100) * bbox["height"]
    end_x = bbox["x"] + (end_pos["x"] / 100) * bbox["width"]
    end_y = bbox["y"] + (end_pos["y"] / 100) * bbox["height"]

    page_session.mouse.move(start_x, start_y)
    page_session.mouse.down(button=button)
    page_session.mouse.move(end_x, end_y)
    page_session.mouse.up(button=button)
    page_session.wait_for_timeout(500)


@pytest.mark.usefixtures("solara_test")
def test_jupyter_set_view_state(page_session, sample_map):
    """Test setting view state in Jupyter environment."""
    m = sample_map
    set_state = {
        "longitude": -100,
        "latitude": 40,
        "zoom": 5,
        "pitch": 30,
        "bearing": 45,
    }
    m.set_view_state(**set_state)

    # Simulate a cell break in Jupyter, best I could do
    display(m)
    canvas = page_session.locator("canvas").first
    canvas.wait_for(timeout=5000)
    page_session.wait_for_timeout(1000)

    assert m.view_state == MapViewState(**set_state)


@pytest.mark.usefixtures("solara_test")
def test_jupyter_manual_view_state_change(page_session, sample_map):
    """Test manual view state change in Jupyter environment."""
    m = sample_map
    m.set_view_state(zoom=3)
    display(m)
    initial_view_state = m.view_state
    start_pos = {"x": 50, "y": 50}

    # Increase lon from 0 by dragging left
    end_pos = {"x": 40, "y": 50}
    click_and_drag_canvas(page_session, start_pos, end_pos, button="left")
    assert m.view_state.longitude > initial_view_state.longitude

    # Increse lat from 0 by dragging down
    end_pos = {"x": 50, "y": 60}
    click_and_drag_canvas(page_session, start_pos, end_pos, button="left")
    assert m.view_state.latitude > initial_view_state.latitude

    # Increase pitch by dragging up w. RMB
    end_pos = {"x": 50, "y": 40}
    click_and_drag_canvas(page_session, start_pos, end_pos, button="right")
    assert m.view_state.pitch > initial_view_state.pitch

    # Increase bearing by dragging left w. RMB
    start_pos = {"x": 40, "y": 40}
    end_pos = {"x": 30, "y": 40}
    click_and_drag_canvas(page_session, start_pos, end_pos, button="right")
    assert m.view_state.bearing > initial_view_state.bearing

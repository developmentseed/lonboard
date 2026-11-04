"""Setting the view state from Python moves a map that is already displayed.

Regression tests for https://github.com/developmentseed/lonboard/issues/1062 and
https://github.com/developmentseed/lonboard/issues/1024
"""

import io
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

import geopandas as gpd
import ipywidgets
import pytest
import shapely
from IPython.display import display
from PIL import Image
from playwright.sync_api import Locator, Page
from shapely.geometry import box
from test_utils import setup_map_widget, wait_for_canvas

from lonboard import Map
from lonboard.basemap import MaplibreBasemap
from lonboard.experimental.view import BaseView, GlobeView
from lonboard.layer import SolidPolygonLayer
from lonboard.view_state import GlobeViewState, MapViewState

BASEMAP_MODES = ["overlaid", "interleaved", "reverse-controlled"]

INITIAL_VIEW_STATE: dict[str, float] = {"longitude": 0, "latitude": 0, "zoom": 3}
TARGET_VIEW_STATE: dict[str, float] = {"longitude": 100, "latitude": 0, "zoom": 3}

# A polygon under the center of the initial view, to know when the map has rendered
ORIGIN_COLOR = (0, 120, 200)
ORIGIN_POLYGON = box(-5, -5, 5, 5)

# A polygon far outside of the initial view, to know when the map has moved there
TARGET_COLOR = (200, 0, 80)
TARGET_POLYGON = box(95, -5, 105, 5)

# Dragging the map 200px to the left at zoom 3 moves the center of the map
# 200 / (512 * 2**3) * 360 = 17.6 degrees to the east
DRAG_PIXELS = 200
DRAG_DEGREES = 17.6

# Longer than the 300ms debounce of view state updates from the map to Python
TIMEOUT_VIEW_STATE_SYNC = 1000


def solid_layer(
    polygon: shapely.Polygon,
    color: tuple[int, int, int],
    *,
    elevation: float | None = None,
) -> SolidPolygonLayer:
    if elevation is not None:
        polygon = shapely.force_3d(polygon, z=elevation)
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
    return SolidPolygonLayer.from_geopandas(gdf, get_fill_color=list(color))


def make_map(
    mode: str,
    *,
    target_polygon: shapely.Polygon = TARGET_POLYGON,
    view: BaseView | None = None,
    elevation: float | None = None,
) -> Map:
    """Create a map with a polygon at the initial view and one where it will move."""
    return Map(
        [
            solid_layer(ORIGIN_POLYGON, ORIGIN_COLOR, elevation=elevation),
            solid_layer(target_polygon, TARGET_COLOR, elevation=elevation),
        ],
        # The view has to be set before the view state, as it defines its type
        view=view,
        view_state=INITIAL_VIEW_STATE,
        basemap=MaplibreBasemap(mode=mode),
    )


def center(element: Locator) -> tuple[float, float]:
    element_box = element.bounding_box()
    assert element_box is not None
    x = element_box["x"] + element_box["width"] / 2
    y = element_box["y"] + element_box["height"] / 2
    return (x, y)


def center_pixel(page: Page, element: Locator) -> tuple[int, int, int]:
    x, y = center(element)
    png = page.screenshot(clip={"x": x, "y": y, "width": 1, "height": 1})
    pixel = Image.open(io.BytesIO(png)).convert("RGB").getpixel((0, 0))
    assert isinstance(pixel, tuple)
    r, g, b = pixel
    return (r, g, b)


def color_matches(pixel: tuple[int, int, int], expected: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= 2 for a, b in zip(pixel, expected, strict=True))


def assert_centered_on(
    page: Page,
    element: Locator,
    expected: tuple[int, int, int],
    message: str,
    timeout: float = 10,
) -> None:
    """Poll the pixel at the center of `element` until it matches `expected`."""
    deadline = time.monotonic() + timeout
    pixel = center_pixel(page, element)
    while not color_matches(pixel, expected) and time.monotonic() < deadline:
        page.wait_for_timeout(250)
        pixel = center_pixel(page, element)

    assert color_matches(pixel, expected), (
        f"{message}: center pixel is {pixel}, expected {expected}"
    )


def assert_stays_centered_on(
    page: Page,
    element: Locator,
    expected: tuple[int, int, int],
    message: str,
    duration: float = 1,
) -> None:
    """Check the pixel at the center of `element` repeatedly for `duration` seconds."""
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        assert_centered_on(page, element, expected, message, timeout=0)
        page.wait_for_timeout(100)


def wait_for_initial_view(page: Page, element: Locator) -> None:
    """Wait until the map in `element` is displayed and in sync with Python."""
    assert_centered_on(
        page,
        element,
        ORIGIN_COLOR,
        "Map never rendered the initial view",
    )
    # The map sends its view state to Python once after it has loaded
    page.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)


def assert_view_state(m: Map, expected: dict[str, float]) -> None:
    assert m.view_state is not None
    for name, value in expected.items():
        assert getattr(m.view_state, name) == pytest.approx(value, abs=1e-6), (
            f"Expected view_state.{name} to be {value}, got {m.view_state}"
        )


def record_view_states_from_browser(monkeypatch: pytest.MonkeyPatch, m: Map) -> list:
    """Record every view state that the map in the browser sends to Python."""
    view_states = []
    set_state = m.set_state

    def record_and_set_state(sync_data: dict) -> None:
        if "view_state" in sync_data:
            view_states.append(sync_data["view_state"])
        set_state(sync_data)

    monkeypatch.setattr(m, "set_state", record_and_set_state)
    return view_states


@contextmanager
def hold_view_states_from_browser(
    monkeypatch: pytest.MonkeyPatch,
    m: Map,
) -> Iterator[threading.Semaphore]:
    """Make Python wait before it handles a view state that the browser sends.

    This is what a slow kernel looks like to the map. Python handles one view state,
    and sends it back to the map, for every `release()` of the semaphore.
    """
    held_view_states = threading.Semaphore(0)
    set_state = m.set_state

    def wait_and_set_state(sync_data: dict) -> None:
        if "view_state" in sync_data:
            held_view_states.acquire(timeout=30)
        set_state(sync_data)

    monkeypatch.setattr(m, "set_state", wait_and_set_state)
    try:
        yield held_view_states
    finally:
        # Don't keep Python waiting when the test has failed
        monkeypatch.setattr(m, "set_state", set_state)
        held_view_states.release(16)


def display_side_by_side(page: Page, map_a: Map, map_b: Map) -> tuple[Locator, Locator]:
    """Display two maps next to each other, as `examples/linked-maps.ipynb` does."""
    map_a.layout = ipywidgets.Layout(flex="1")
    map_b.layout = ipywidgets.Layout(flex="1")
    display(ipywidgets.HBox([map_a, map_b]))
    wait_for_canvas(page)

    maps = page.locator(".lonboard")
    maps.nth(1).wait_for()
    return maps.nth(0), maps.nth(1)


def press_and_drag(page: Page, element: Locator, dx: float) -> None:
    """Drag the map in `element` by `dx` pixels and keep the mouse button down."""
    x, y = center(element)
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx, y, steps=10)


def drag(page: Page, element: Locator, dx: float) -> None:
    """Drag the map in `element` by `dx` pixels."""
    press_and_drag(page, element, dx)
    # Hold still before releasing so that the map doesn't keep moving with inertia
    page.wait_for_timeout(200)
    page.mouse.up()


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_set_view_state_moves_displayed_map(
    page_session: Page,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
):
    m = make_map(mode)
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)
    view_states_from_browser = record_view_states_from_browser(monkeypatch, m)

    view_state = {**TARGET_VIEW_STATE, "pitch": 30, "bearing": 45}
    m.set_view_state(**view_state)

    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map did not move after set_view_state",
    )
    # The map must not send the view state that Python set back to Python
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert view_states_from_browser == []
    assert_view_state(m, view_state)


@pytest.mark.usefixtures("solara_test")
def test_set_view_state_moves_displayed_globe(page_session: Page):
    # A globe view is only supported in interleaved mode. The polygons are raised
    # above the surface of the globe, which would otherwise hide them.
    m = make_map("interleaved", view=GlobeView(), elevation=200_000)
    assert isinstance(m.view_state, GlobeViewState)
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)

    m.set_view_state(**TARGET_VIEW_STATE)

    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map did not move after set_view_state",
    )
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert_view_state(m, TARGET_VIEW_STATE)


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_pan_is_not_reverted_by_python(page_session: Page, mode: str):
    """Python sending a panned view state back to the map doesn't move the map."""
    # Only the center of the view after panning twice is inside of the polygon
    m = make_map(mode, target_polygon=box(29, -5, 41, 5))
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)

    drag(page_session, canvas, dx=-DRAG_PIXELS)
    # In reverse-controlled mode, which debounces the first pan, Python sends it
    # back to the map while the mouse button is still down for the second pan
    press_and_drag(page_session, canvas, dx=-DRAG_PIXELS)
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map moved while panning",
        timeout=0,
    )
    page_session.mouse.up()

    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map moved after panning",
        timeout=0,
    )
    assert isinstance(m.view_state, MapViewState)
    assert m.view_state.longitude == pytest.approx(2 * DRAG_DEGREES, abs=6)


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", ["overlaid", "interleaved"])
def test_pan_is_not_reverted_by_late_python(
    page_session: Page,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
):
    """Python sending a pan back after the next pan has ended doesn't move the map."""
    # Only the center of the view after panning twice is inside of the polygon
    m = make_map(mode, target_polygon=box(29, -5, 41, 5))
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)

    with hold_view_states_from_browser(monkeypatch, m) as held_view_states:
        drag(page_session, canvas, dx=-DRAG_PIXELS)
        # So that the map sends the first pan to Python before the second pan starts
        page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
        drag(page_session, canvas, dx=-DRAG_PIXELS)
        page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
        assert_centered_on(
            page_session,
            canvas,
            TARGET_COLOR,
            "Map did not pan",
            timeout=0,
        )
        assert_view_state(m, INITIAL_VIEW_STATE)

        # Python handles the first pan only now, and sends it back to the map
        held_view_states.release()
        assert_stays_centered_on(
            page_session,
            canvas,
            TARGET_COLOR,
            "Map moved back to the first pan",
        )
        assert isinstance(m.view_state, MapViewState)
        assert m.view_state.longitude == pytest.approx(DRAG_DEGREES, abs=1)

        # Then Python handles the second pan
        held_view_states.release()
        assert_stays_centered_on(
            page_session,
            canvas,
            TARGET_COLOR,
            "Map moved after the second pan",
        )

    assert isinstance(m.view_state, MapViewState)
    assert m.view_state.longitude == pytest.approx(2 * DRAG_DEGREES, abs=1)


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_set_view_state_back_to_panned_view(page_session: Page, mode: str):
    """Python can move the map back to a view that the map was panned to before."""
    # Only the center of the view after panning once is inside of the polygon
    m = make_map(mode, target_polygon=box(10, -5, 25, 5))
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)

    drag(page_session, canvas, dx=-DRAG_PIXELS)
    assert_centered_on(page_session, canvas, TARGET_COLOR, "Map did not pan")
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    panned_view_state = m.view_state
    assert isinstance(panned_view_state, MapViewState)
    assert panned_view_state.longitude == pytest.approx(DRAG_DEGREES, abs=2)

    m.set_view_state(**INITIAL_VIEW_STATE)
    assert_centered_on(
        page_session,
        canvas,
        ORIGIN_COLOR,
        "Map did not move to the initial view",
    )

    m.set_view_state(panned_view_state)
    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map did not move back to the panned view",
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_set_view_state_back_to_earlier_pan(page_session: Page, mode: str):
    """Python can move the map back to a view from before the map was panned again."""
    # Only the center of the view after panning once is inside of the polygon
    m = make_map(mode, target_polygon=box(10, -5, 25, 5))
    canvas = setup_map_widget(page_session, m)
    wait_for_initial_view(page_session, canvas)

    drag(page_session, canvas, dx=-DRAG_PIXELS)
    assert_centered_on(page_session, canvas, TARGET_COLOR, "Map did not pan")
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    first_pan_view_state = m.view_state
    assert isinstance(first_pan_view_state, MapViewState)
    assert first_pan_view_state.longitude == pytest.approx(DRAG_DEGREES, abs=2)

    drag(page_session, canvas, dx=-DRAG_PIXELS)
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert isinstance(m.view_state, MapViewState)
    assert m.view_state.longitude > first_pan_view_state.longitude + 10

    m.set_view_state(first_pan_view_state)
    assert_centered_on(
        page_session,
        canvas,
        TARGET_COLOR,
        "Map did not move back to the first pan",
    )


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_linked_maps_set_from_python(page_session: Page, mode: str):
    map_a = make_map(mode)
    map_b = make_map(mode)
    map_a.observe(
        lambda change: map_b.set_view_state(change["new"]),
        names="view_state",
    )
    element_a, element_b = display_side_by_side(page_session, map_a, map_b)
    wait_for_initial_view(page_session, element_a)
    wait_for_initial_view(page_session, element_b)

    map_a.set_view_state(**TARGET_VIEW_STATE)

    assert_centered_on(page_session, element_a, TARGET_COLOR, "Map A did not move")
    assert_centered_on(page_session, element_b, TARGET_COLOR, "Map B did not move")
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert_view_state(map_a, TARGET_VIEW_STATE)
    assert_view_state(map_b, TARGET_VIEW_STATE)


def link_in_python(map_a: Map, map_b: Map) -> None:
    """Link the view states of two maps, as `examples/linked-maps.ipynb` does."""
    map_a.observe(
        lambda change: map_b.set_view_state(change["new"]),
        names="view_state",
    )
    map_b.observe(
        lambda change: map_a.set_view_state(change["new"]),
        names="view_state",
    )


def link_in_browser(map_a: Map, map_b: Map) -> None:
    """Link the view states of two maps without a round trip to Python."""
    ipywidgets.jslink((map_a, "view_state"), (map_b, "view_state"))


@pytest.mark.usefixtures("solara_test")
@pytest.mark.parametrize(
    "link",
    [link_in_python, link_in_browser],
    ids=["observe", "jslink"],
)
@pytest.mark.parametrize("mode", BASEMAP_MODES)
def test_linked_maps_pan_in_browser(
    page_session: Page,
    request: pytest.FixtureRequest,
    mode: str,
    link: Callable[[Map, Map], None],
):
    """Panning one map moves the other one."""
    if mode == "reverse-controlled" and link is link_in_browser:
        request.applymarker(
            pytest.mark.xfail(
                reason="Deck-first maps linked by jslink send each other older view "
                "states while one is dragged, so part of the drag is lost",
            ),
        )
    # Only the center of the view after panning once is inside of the polygon
    map_a = make_map(mode, target_polygon=box(10, -5, 25, 5))
    map_b = make_map(mode, target_polygon=box(10, -5, 25, 5))
    link(map_a, map_b)
    element_a, element_b = display_side_by_side(page_session, map_a, map_b)
    wait_for_initial_view(page_session, element_a)
    wait_for_initial_view(page_session, element_b)

    drag(page_session, element_a, dx=-DRAG_PIXELS)

    assert_centered_on(page_session, element_a, TARGET_COLOR, "Map A did not move")
    assert_centered_on(page_session, element_b, TARGET_COLOR, "Map B did not move")

    # Both maps stay at the view state of the map that was panned
    page_session.wait_for_timeout(TIMEOUT_VIEW_STATE_SYNC)
    assert_centered_on(
        page_session,
        element_a,
        TARGET_COLOR,
        "Map A moved back",
        timeout=0,
    )
    assert_centered_on(
        page_session,
        element_b,
        TARGET_COLOR,
        "Map B moved back",
        timeout=0,
    )
    assert isinstance(map_a.view_state, MapViewState)
    assert map_a.view_state.longitude == pytest.approx(DRAG_DEGREES, abs=2)
    assert map_a.view_state == map_b.view_state

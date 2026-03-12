# ruff: noqa: SLF001

from __future__ import annotations

import asyncio
import traceback
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
    cast,
)

import traitlets.traitlets as t
from ipywidgets.widgets.trait_types import TypedTuple

# Import from source to allow mkdocstrings to link to base class
from ipywidgets.widgets.widget_box import VBox

from lonboard._base import BaseWidget

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ipywidgets import FloatRangeSlider


class MultiRangeSlider(VBox):
    """A widget for multiple ranged sliders.

    This is designed to be used with the
    [DataFilterExtension][lonboard.layer_extension.DataFilterExtension] when you want to
    filter on 2 to 4 columns on the same time.

    If you have only a single filter, use an ipywidgets
    [FloatRangeSlider][ipywidgets.widgets.widget_float.FloatRangeSlider] directly.

    **Example:**

    ```py
    from ipywidgets import FloatRangeSlider

    slider1 = FloatRangeSlider(
        value=(2, 5),
        min=0,
        max=10,
        step=0.1,
        description="First slider: "
    )
    slider2 = FloatRangeSlider(
        value=(30, 40),
        min=0,
        max=50,
        step=1,
        description="Second slider: "
    )
    multi_slider = MultiRangeSlider([slider1, slider2])
    multi_slider
    ```

    Then to propagate updates to a rendered layer, call
    [jsdlink][ipywidgets.widgets.widget_link.jsdlink] to connect the two widgets.

    ```py
    from ipywidgets import jsdlink

    jsdlink(
        (multi_slider, "value"),
        (layer, "filter_range")
    )
    ```

    As you change the slider, the `filter_range` value on the layer class should be
    updated.
    """

    # We use a tuple to force reassignment to update the list
    # This is because list mutations do not get propagated as events
    # https://github.com/jupyter-widgets/ipywidgets/blob/b2531796d414b0970f18050d6819d932417b9953/python/ipywidgets/ipywidgets/widgets/widget_box.py#L52-L54
    value = TypedTuple(trait=TypedTuple(trait=t.Float())).tag(sync=True)

    def __init__(self, children: Sequence[FloatRangeSlider], **kwargs: Any) -> None:
        """Create a new MultiRangeSlider."""
        if len(children) == 1:
            raise ValueError(
                "Expected more than one slider. "
                "For filtering data from a single column, "
                "use a FloatRangeSlider directly.",
            )

        # We manage a list of lists to match what deck.gl expects for the
        # DataFilterExtension
        def callback(change: dict, *, i: int) -> None:
            value = list(self.value)
            value[i] = change["new"]
            self.set_trait("value", value)
            self.send_state("value")

        initial_values = []
        for i, child in enumerate(children):
            func = partial(callback, i=i)
            child.observe(func, "value")
            initial_values.append(child.value)

        super().__init__(children, value=initial_values, **kwargs)


class BaseControl(BaseWidget):
    """A deck.gl or Maplibre Control."""

    position = t.Union(
        [
            t.Unicode("top-left"),
            t.Unicode("top-right"),
            t.Unicode("bottom-left"),
            t.Unicode("bottom-right"),
        ],
        allow_none=True,
        default_value=None,
    ).tag(sync=True)
    """Position of the control in the map.

    One of `"top-left"`, `"top-right"`, `"bottom-left"`, or `"bottom-right"`.
    """


class FullscreenControl(BaseControl):
    """A deck.gl FullscreenControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a button to the map
    that allows for toggling fullscreen mode.
    """

    _control_type = t.Unicode("fullscreen").tag(sync=True)


GEOCODER_MSG_KIND: Final = "geocoder-query"


class _GeocoderRequestMessage(TypedDict):
    query: str


class _GeocoderRequest(TypedDict):
    id: str
    kind: Literal["geocoder-query"]
    msg: _GeocoderRequestMessage


def _on_geocoder_dispatch(
    widget: GeocoderControl,
    msg: str | list | dict,
    buffers: list[bytes],  # noqa: ARG001
) -> None:
    if not isinstance(msg, dict) or msg.get("kind") != GEOCODER_MSG_KIND:
        return

    # Schedule the async handler on the event loop
    task = asyncio.create_task(
        _handle_geocoder_request(widget, cast("_GeocoderRequest", msg)),
    )
    widget._pending_tasks.add(task)
    task.add_done_callback(widget._pending_tasks.discard)


async def _handle_geocoder_request(
    widget: GeocoderControl,
    msg: _GeocoderRequest,
) -> None:
    output = widget._error_output

    try:
        output.append_stdout(f"Received tile request: {msg}")
        query = msg["msg"]["query"]
        response = await widget._client(query)
        widget.send(
            {
                "id": msg["id"],
                "kind": f"{GEOCODER_MSG_KIND}-response",
                "response": response,
            },
        )

    except Exception:  # noqa: BLE001
        error_msg = traceback.format_exc()
        output.append_stderr(f"Error handling tile request: {error_msg}\n")

        widget.send(
            {
                "id": msg["id"],
                "kind": f"{GEOCODER_MSG_KIND}-response",
                "response": {"error": error_msg},
            },
        )


class GeoJsonPoint(TypedDict):
    """A GeoJSON Point geometry."""

    type: Literal["Point"]

    coordinates: tuple[float, float]
    """The coordinates of the point, in [longitude, latitude] order."""


class GeocoderResponse(TypedDict):
    """The expected response from a geocoder query.

    This must be a GeoJSON Point feature, extended with some additional properties.
    """

    type: Literal["Feature"]

    id: NotRequired[Any]

    properties: dict[str, Any]

    geometry: GeoJsonPoint

    text: str
    """Text representing the feature (e.g. "Austin")."""

    language: NotRequired[str]
    """The language code of the text returned in text."""

    place_name: str
    """Human-readable text representing the full result hierarchy.

    For example, "Austin, Texas, United States".
    """

    place_type: Sequence[str]
    """An array of index types that this feature may be returned as.

    Most features have only one type matching its id.
    """

    bbox: NotRequired[tuple[float, float, float, float]]
    """Bounding box of the form [minx,miny,maxx,maxy]."""

    center: NotRequired[tuple[float, float]]
    """The center of the feature [lng, lat]."""


class GeocoderHandler(Protocol):
    """A protocol for handling geocoder queries from the frontend."""

    async def __call__(self, query: str) -> GeocoderResponse:
        """Handle a geocoder query.

        Args:
            query: The geocoder query string from the frontend.

        """
        ...


class GeocoderControl(BaseControl):
    """A deck.gl GeocoderControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a geocoder search
    box to the map.
    """

    _pending_tasks: set[asyncio.Task[None]]
    _client: GeocoderHandler

    def __init__(self, client: GeocoderHandler, **kwargs: Any) -> None:
        self._client = client
        self.on_msg(_on_geocoder_dispatch)
        self._pending_tasks = set()

        super().__init__(**kwargs)

    @classmethod
    def from_geopy(cls, geocoder: Any, **kwargs: Any) -> GeocoderControl:
        """Create a GeocoderControl from a geopy geocoder instance."""
        # async def handler(query: str) -> GeocoderResponse:
        #     loop = asyncio.get_event_loop()
        #     result = await loop.run_in_executor(None, geocoder.geocode, query)
        #     if result is None:
        #         raise ValueError(f"Geocoding query '{query}' returned no results")
        #     return {
        #         "type": "Feature",
        #         "properties": {"name": result.address},
        #         "text": result.address,
        #         "place_name": result.address,
        #         "place_type": ["geopy-result"],
        #         "center": (result.longitude, result.latitude),
        #     }

        raise NotImplementedError
        # return cls(client=handler, **kwargs)

    _control_type = t.Unicode("geocoder").tag(sync=True)


class NavigationControl(BaseControl):
    """A deck.gl NavigationControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add zoom and compass
    buttons to the map.
    """

    _control_type = t.Unicode("navigation").tag(sync=True)

    show_compass = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the compass button.

    Default `True`.
    """

    show_zoom = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to show the zoom buttons.

    Default `True`.
    """

    visualize_pitch = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable pitch visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `True`.
    """

    visualize_roll = t.Bool(allow_none=True, default_value=None).tag(sync=True)
    """Whether to enable roll visualization.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `False`.
    """


class ScaleControl(BaseControl):
    """A deck.gl ScaleControl.

    Passing this to [`Map.controls`][lonboard.Map.controls] will add a scale bar to the
    map.
    """

    _control_type = t.Unicode("scale").tag(sync=True)

    max_width = t.Int(allow_none=True, default_value=None).tag(sync=True)
    """The maximum width of the scale control in pixels.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    Default `100`.
    """

    unit = t.Unicode(allow_none=True, default_value=None).tag(sync=True)
    """The unit of the scale.

    This only has effect for Maplibre-driven maps (i.e. where
    [`MaplibreBasemap.mode`][lonboard.basemap.MaplibreBasemap.mode] is "overlaid" or
    "interleaved").

    One of `'metric'`, `'imperial'`, or `'nautical'`. Default is `'metric'`.
    """

# ruff: noqa: SLF001

from __future__ import annotations

import asyncio
import traceback
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

from lonboard.controls._base import BaseControl

if TYPE_CHECKING:
    from collections.abc import Sequence

    from geopy.geocoders.base import Geocoder


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
        if widget.debug:
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


class GeocoderFeature(TypedDict):
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


class GeocoderFeatureCollection(TypedDict):
    """A collection of geocoder features."""

    type: Literal["FeatureCollection"]

    features: Sequence[GeocoderFeature]
    """The geocoder features returned from the query."""


class GeocoderHandler(Protocol):
    """A protocol for handling geocoder queries from the frontend."""

    async def __call__(
        self,
        query: str,
    ) -> GeocoderFeatureCollection | GeocoderFeature | None:
        """Handle a geocoder query.

        Args:
            query: The geocoder query string from the frontend.

        Returns:
            A `FeatureCollection` or `Feature` to return to the frontend. Return a FeatureCollection if there are multiple results found.

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
    def from_geopy(cls, geocoder: Geocoder, **kwargs: Any) -> GeocoderControl:
        """Create a GeocoderControl from a [geopy][geopy] geocoder instance.

        The geocoder must be created in [async mode] using an async adapter (e.g.
        [`AioHTTPAdapter`][geopy.adapters.AioHTTPAdapter]).

        [async mode]: https://geopy.readthedocs.io/en/stable/#async-mode

        **Example:**

        ```py
        from lonboard.controls import GeocoderControl
        from lonboard import Map
        from geopy.adapters import AioHTTPAdapter
        from geopy.geocoders import Nominatim

        geocoder = Nominatim(user_agent="lonboard", adapter_factory=AioHTTPAdapter)
        geocoder_control = GeocoderControl.from_geopy(geocoder)

        m = Map(layer, controls=[geocoder_control])
        ```
        """
        from geopy.adapters import BaseAsyncAdapter
        from geopy.location import Location

        if not isinstance(geocoder.adapter, BaseAsyncAdapter):
            msg = (
                "The geopy geocoder must be created in async mode.\n"
                "Pass `adapter_factory=AioHTTPAdapter` to the geocoder constructor.\n"
                "See https://geopy.readthedocs.io/en/stable/#async-mode for more info.",
            )
            raise TypeError(msg)

        def convert_location(location: Location) -> GeocoderFeature:
            return {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": (location.longitude, location.latitude),
                },
                "text": location.address,
                "place_name": location.address,
                "place_type": ["geopy-result"],
                "center": (location.longitude, location.latitude),
            }

        async def handler(
            query: str,
        ) -> GeocoderFeatureCollection | GeocoderFeature | None:
            location = await geocoder.geocode(query, exactly_one=False)
            if location is None:
                return None

            if isinstance(location, list):
                locations = [convert_location(loc) for loc in location]
                return {
                    "type": "FeatureCollection",
                    "features": locations,
                }

            if isinstance(location, Location):
                return convert_location(location)

            raise TypeError(f"Unexpected geopy result type: {location}")

        return cls(client=handler, **kwargs)

    _control_type = t.Unicode("geocoder").tag(sync=True)

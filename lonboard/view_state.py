from __future__ import annotations

from dataclasses import dataclass


class BaseViewState:
    """Base class for view states."""


@dataclass(frozen=True)
class MapViewState(BaseViewState):
    """State of a [MapView][lonboard.experimental.view.MapView]."""

    longitude: float = 0
    """longitude at the map center"""

    latitude: float = 10
    """latitude at the map center."""

    zoom: float = 0.5
    """zoom level."""

    pitch: float = 0
    """pitch angle in degrees. `0` is top-down."""

    bearing: float = 0
    """bearing angle in degrees. `0` is north."""

    max_zoom: float = 20
    """max zoom level."""

    min_zoom: float = 0
    """min zoom level."""

    max_pitch: float = 60
    """max pitch angle."""

    min_pitch: float = 0
    """min pitch angle."""


@dataclass(frozen=True)
class GlobeViewState(BaseViewState):
    """State of a [GlobeView][lonboard.experimental.view.GlobeView]."""

    longitude: float
    """longitude at the viewport center."""

    latitude: float
    """latitude at the viewport center."""

    zoom: float
    """zoom level."""

    max_zoom: float = 20
    """max zoom level. Default 20."""

    min_zoom: float = 0
    """min zoom level. Default 0."""


@dataclass(frozen=True)
class FirstPersonViewState(BaseViewState):
    """State of a [FirstPersonView][lonboard.experimental.view.FirstPersonView]."""

    longitude: float
    """longitude of the camera position."""

    latitude: float
    """latitude of the camera position."""

    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """Meter offsets of the camera from the lng-lat anchor point."""

    bearing: float = 0.0
    """bearing angle in degrees. `0` is north."""

    pitch: float = 0.0
    """pitch angle in degrees. `0` is horizontal."""

    max_pitch: float = 90.0
    """max pitch angle. Default 90 (down)."""

    min_pitch: float = -90.0
    """min pitch angle. Default -90 (up)."""


@dataclass(frozen=True)
class OrthographicViewState(BaseViewState):
    """State of an [OrthographicView][lonboard.experimental.view.OrthographicView]."""

    target: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """The world position at the center of the viewport."""

    zoom: float | tuple[float, float] = 0.0
    """The zoom level of the viewport.

    - `zoom: 0` maps one unit distance to one pixel on screen, and increasing `zoom` by `1` scales the same object to twice as large. For example `zoom: 1` is 2x the original size, `zoom: 2` is 4x, `zoom: 3` is 8x etc.

    To apply independent zoom levels to the X and Y axes, supply a tuple [zoomX, zoomY].

    Default 0.
    """

    min_zoom: float | None = None
    """The min zoom level of the viewport. Default -Infinity."""

    max_zoom: float | None = None
    """The max zoom level of the viewport. Default Infinity."""


@dataclass(frozen=True)
class OrbitViewState(BaseViewState):
    """State of an [OrbitView][lonboard.experimental.view.OrbitView]."""

    target: tuple[float, float, float] = (0.0, 0.0, 0.0)
    """The world position at the center of the viewport."""

    rotation_orbit: float = 0.0
    """Rotating angle around orbit axis. Default 0."""

    rotation_x: float = 0.0
    """Rotating angle around X axis. Default 0."""

    zoom: float = 0.0
    """The zoom level of the viewport.

    `zoom: 0` maps one unit distance to one pixel on screen, and increasing `zoom` by
    `1` scales the same object to twice as large.

    Default 0.
    """

    min_zoom: float | None = None
    """The min zoom level of the viewport. Default -Infinity."""

    max_zoom: float | None = None
    """The max zoom level of the viewport. Default Infinity."""

    min_rotation_x: float = -90.0
    """The min rotating angle around X axis. Default -90."""

    max_rotation_x: float = 90.0
    """The max rotating angle around X axis. Default 90."""

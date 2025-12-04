/** Check for null and undefined */

import {
  _GlobeView as GlobeView,
  GlobeViewState,
  MapView,
  MapViewState,
} from "@deck.gl/core";

import { MapRendererProps } from "./renderers";

// https://stackoverflow.com/a/52097445
export function isDefined<T>(value: T | undefined | null): value is T {
  return value !== undefined && value !== null;
}

export function makePolygon(pt1: number[], pt2: number[]) {
  return [pt1, [pt1[0], pt2[1]], pt2, [pt2[0], pt1[1]], pt1];
}

export function isGlobeView(views: MapRendererProps["views"]) {
  const firstView = Array.isArray(views) ? views[0] : views;
  return firstView instanceof GlobeView;
}

export function isMapView(views: MapRendererProps["views"]) {
  const firstView = Array.isArray(views) ? views[0] : views;
  return firstView instanceof MapView;
}

export function sanitizeViewState(
  views: MapRendererProps["views"],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  viewState: (MapViewState | GlobeViewState) & Record<string, any>,
): MapViewState | GlobeViewState {
  const sanitized: MapViewState | GlobeViewState = {
    longitude: Number.isFinite(viewState.longitude) ? viewState.longitude : 0,
    latitude: Number.isFinite(viewState.latitude) ? viewState.latitude : 0,
    zoom: Number.isFinite(viewState.zoom) ? viewState.zoom : 0,
    ...(Number.isFinite(viewState.minZoom)
      ? {
          minZoom: viewState.minZoom,
        }
      : 0),
    ...(Number.isFinite(viewState.maxZoom)
      ? {
          maxZoom: viewState.maxZoom,
        }
      : 0),

    // Only include pitch & bearing if defined in ViewState
    ...("pitch" in viewState && Number.isFinite(viewState.pitch)
      ? { pitch: viewState.pitch }
      : {}),
    ...("bearing" in viewState && Number.isFinite(viewState.bearing)
      ? { bearing: viewState.bearing }
      : {}),
  };
  return sanitized;
}

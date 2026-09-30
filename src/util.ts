/** Check for null and undefined */

import type { GlobeViewState, MapViewState } from "@deck.gl/core";
import { _GlobeView as GlobeView, MapView } from "@deck.gl/core";

import type { MapRendererProps } from "./renderers";

// https://stackoverflow.com/a/52097445
export function isDefined<T>(value: T | undefined | null): value is T {
  return value !== undefined && value !== null;
}

/**
 * Drop keys whose value is `null` or `undefined`.
 *
 * deck.gl copies an explicit `undefined` over a layer's default props, so
 * passing an unset prop through as `undefined` would shadow the default
 * instead of falling back to it. Passing only the defined props lets deck.gl's
 * defaults apply.
 */
export function omitUndefined<T extends object>(
  obj: T,
): { [K in keyof T]?: NonNullable<T[K]> } {
  const result: { [K in keyof T]?: NonNullable<T[K]> } = {};
  for (const key in obj) {
    const value = obj[key];
    if (value !== undefined && value !== null) {
      result[key] = value;
    }
  }
  return result;
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
  _views: MapRendererProps["views"],
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
    ...(Number.isFinite(viewState.pitch)
      ? {
          pitch: viewState.pitch,
        }
      : 0),
    ...(Number.isFinite(viewState.bearing)
      ? {
          bearing: viewState.bearing,
        }
      : 0),
  };
  return sanitized;
}

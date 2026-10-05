import type { GlobeViewState, MapViewState } from "@deck.gl/core";
import { _GlobeView as GlobeView, MapView } from "@deck.gl/core";

import type { MapRendererProps } from "./renderers";

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

/** The parts of a view state that position the camera. */
const CAMERA_KEYS = [
  "longitude",
  "latitude",
  "zoom",
  "pitch",
  "bearing",
] as const;

export type Camera = Partial<Pick<MapViewState, (typeof CAMERA_KEYS)[number]>>;

/**
 * The view state to send to Python after the map has moved: `current`, the
 * view state that Python has, with its camera moved to `camera`.
 *
 * Keeping the other keys of `current`, such as `maxZoom`, means that Python
 * serializes the view state to exactly what it received, so it doesn't send
 * it back to the map. Keys that `current` doesn't have aren't added, because
 * not every view state has all of them. E.g. a globe view state has no pitch
 * or bearing. Transition keys, such as those that `flyTo` sets, are dropped,
 * as Python drops them too.
 */
export function moveViewState<T extends Record<string, unknown>>(
  current: T | null | undefined,
  camera: Camera,
): T | Camera {
  if (!current) return camera;

  const moved: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(current)) {
    if (!key.startsWith("transition")) {
      moved[key] = value;
    }
  }
  for (const key of CAMERA_KEYS) {
    if (key in current && Number.isFinite(camera[key])) {
      moved[key] = camera[key];
    }
  }
  return moved as T;
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

export function getRepeat(views: MapRendererProps["views"]) {
  const firstView = Array.isArray(views) ? views[0] : views;
  return firstView instanceof MapView ? firstView.props.repeat : undefined;
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

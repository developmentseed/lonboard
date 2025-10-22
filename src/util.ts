/** Check for null and undefined */

import { _GlobeView as GlobeView } from "@deck.gl/core";

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

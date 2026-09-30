import type { MapViewState } from "@deck.gl/core";
import { FlyToInterpolator } from "@deck.gl/core";

import type { FlyToMessage } from "../types";
import { omitUndefined } from "../util";

export function flyTo(
  msg: FlyToMessage,
  setInitialViewState: (viewState: MapViewState) => void,
) {
  const {
    longitude,
    latitude,
    zoom,
    pitch,
    bearing,
    transitionDuration,
    curve,
    speed,
    screenSpeed,
  } = msg;
  const transitionInterpolator = new FlyToInterpolator({
    ...omitUndefined({ curve, speed, screenSpeed }),
  });
  setInitialViewState({
    longitude,
    latitude,
    zoom,
    pitch,
    bearing,
    transitionDuration,
    transitionInterpolator,
  });
}

import type { MapViewState } from "@deck.gl/core";
import { FlyToInterpolator } from "@deck.gl/core";

import type { FlyToMessage } from "../types";
import { isDefined } from "../util";

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
    ...(isDefined(curve) && { curve }),
    ...(isDefined(speed) && { speed }),
    ...(isDefined(screenSpeed) && { screenSpeed }),
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

import { FlyToMessage } from "../types";
import { FlyToInterpolator, MapViewState } from "@deck.gl/core";
import { isDefined } from "../util";

export function flyTo(
  msg: FlyToMessage,
  setInitialViewState: (value: MapViewState) => void,
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

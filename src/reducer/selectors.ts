import memoizeOne from "memoize-one";
import { MapMode, State } from ".";
import { PolygonLayer } from "@deck.gl/layers/typed";

/**
 * Comparison helpers (used to memoize selectors)
 */

const compareMapMode = ([state]: [State], [nextState]: [State]) =>
  state.mapMode === nextState.mapMode;

/**
 * Selectors
 */

export const isMapHoverEnabled = memoizeOne(
  (state: State) => state.mapMode === MapMode.BBOX_SELECT_UPDATE,
  compareMapMode,
);

export const isMapClickEnabled = memoizeOne(
  (state: State) =>
    state.mapMode === MapMode.BBOX_SELECT_START ||
    state.mapMode === MapMode.BBOX_SELECT_UPDATE,
  compareMapMode,
);

export const bboxSelectPolygonLayer = memoizeOne(
  (state: State) => {
    if (!state.bboxSelectStart || !state.bboxSelectEnd) {
      return [];
    }

    const [x0, y0] = state.bboxSelectStart;
    const [x1, y1] = state.bboxSelectEnd;

    const polygonLayer = new PolygonLayer({
      id: "bbox-select",
      data: [
        {
          polygon: [
            [x0, y0],
            [x1, y0],
            [x1, y1],
            [x0, y1],
          ],
        },
      ],
      getPolygon: (d) => d.polygon,
      filled: true,
      getFillColor: [0, 0, 0, 50],
      stroked: true,
      getLineWidth: 2,
      lineWidthUnits: "pixels",
    });

    return polygonLayer;
  },
  ([state]: [State], [nextState]: [State]) =>
    state.mapMode === MapMode.PAN ||
    (state.bboxSelectStart === nextState.bboxSelectStart &&
      state.bboxSelectEnd === nextState.bboxSelectEnd),
);

import { type SnapshotFrom } from "xstate";
import { machine } from "./machine";
import { PolygonLayer, PolygonLayerProps } from "@deck.gl/layers/typed";

type Snapshot = SnapshotFrom<typeof machine>;

export const isDrawingBBoxSelection = (state: Snapshot) =>
  state.matches("Selecting bbox start position") ||
  state.matches("Selecting bbox end position");

export const isOnMapHoverEventEnabled = (state: Snapshot) =>
  state.matches("Selecting bbox end position");

export const isTooltipEnabled = (state: Snapshot) => state.matches("Pan mode");

export const getButtonLabel = (state: Snapshot) => {
  if (state.matches("Selecting bbox start position")) {
    return "Click the map to start drawing the selection box";
  } else if (state.matches("Selecting bbox end position")) {
    return "Click the map to finish drawing the selection box";
  }
  return "Click here to start selecting";
};

export const getBboxSelectPolygonLayer = (state: Snapshot) => {
  if (state.context.bboxSelectStart && state.context.bboxSelectEnd) {
    const bboxProps: PolygonLayerProps = {
      id: "bbox-select-polygon",
      data: [
        [
          [state.context.bboxSelectStart[0], state.context.bboxSelectStart[1]],
          [state.context.bboxSelectEnd[0], state.context.bboxSelectStart[1]],
          [state.context.bboxSelectEnd[0], state.context.bboxSelectEnd[1]],
          [state.context.bboxSelectStart[0], state.context.bboxSelectEnd[1]],
        ],
      ],
      getPolygon: (d: any) => d,
      getFillColor: [0, 0, 0, 50],
      getLineColor: [0, 0, 0, 130],
      stroked: true,
      getLineWidth: 2,
      lineWidthUnits: "pixels",
    };
    if (isDrawingBBoxSelection(state)) {
      bboxProps.getFillColor = [255, 255, 0, 120];
      bboxProps.getLineColor = [211, 211, 38, 200];
      bboxProps.getLineWidth = 2;
    }
    return new PolygonLayer(bboxProps);
  }
  return null;
};

export const getBboxSelectBounds = (state: Snapshot) => {
  if (state.context.bboxSelectStart && state.context.bboxSelectEnd) {
    const [x0, y0] = state.context.bboxSelectStart;
    const [x1, y1] = state.context.bboxSelectEnd;
    return [
      Math.min(x0, x1),
      Math.min(y0, y1),
      Math.max(x0, x1),
      Math.max(y0, y1),
    ];
  }
  return null;
};

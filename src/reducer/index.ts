import { DeckGLRef } from "@deck.gl/react/typed";
import { logReducer } from "./utils";
import { PickingInfo } from "@deck.gl/core/typed";

export enum ActionTypes {
  SET_MAP_REF = "SET_MAP_REF",
  MAP_HOVER_EVENT = "MAP_HOVER_EVENT",
  MAP_CLICK_EVENT = "MAP_CLICK_EVENT",
  TOGGLE_BBOX_SELECT_MODE = "TOGGLE_BBOX_SELECT_MODE",
  UPDATE_BBOX_SELECT = "UPDATE_BBOX_SELECT",
}

export enum MapMode {
  PAN = "pan",
  BBOX_SELECT_START = "set-bbox-start",
  BBOX_SELECT_UPDATE = "set-bbox-update",
}

export type Action =
  | {
      type: ActionTypes.SET_MAP_REF;
      data: DeckGLRef;
    }
  | {
      type: ActionTypes.MAP_CLICK_EVENT;
      data: PickingInfo;
    }
  | {
      type: ActionTypes.MAP_HOVER_EVENT;
      data: PickingInfo;
    }
  | {
      type: ActionTypes.TOGGLE_BBOX_SELECT_MODE;
    }
  | {
      type: ActionTypes.UPDATE_BBOX_SELECT;
      data: { bbox: number[] };
    };

export type State = {
  mapRef: DeckGLRef | null;
  mapMode: MapMode;
  selectedObjects: PickingInfo[];
  bboxSelectStart: number[] | undefined;
  bboxSelectStartPixel: number[] | undefined;
  bboxSelectEnd: number[] | undefined;
  bboxSelectEndPixel: number[] | undefined;
};

export const baseInitialState: State = {
  mapRef: null,
  mapMode: MapMode.PAN,
  selectedObjects: [],
  bboxSelectStart: undefined,
  bboxSelectEndPixel: undefined,
  bboxSelectEnd: undefined,
  bboxSelectStartPixel: undefined,
};

export const baseReducer = (
  state: typeof baseInitialState,
  action: Action,
): State => {
  switch (action.type) {
    case ActionTypes.SET_MAP_REF:
      return { ...state, mapRef: action.data };
    case ActionTypes.MAP_CLICK_EVENT:
      if (state.mapMode === MapMode.BBOX_SELECT_START) {
        console.log(action.data);
        return {
          ...state,
          mapMode: MapMode.BBOX_SELECT_UPDATE,
          bboxSelectStart: action.data.coordinate,
          bboxSelectStartPixel: action.data.pixel,
        };
      } else if (state.mapMode === MapMode.BBOX_SELECT_UPDATE) {
        const { bboxSelectStartPixel, bboxSelectEndPixel, mapRef } = state;
        let selectedObjects: PickingInfo[] = [];

        if (bboxSelectStartPixel && bboxSelectEndPixel) {
          const [startX, startY] = bboxSelectStartPixel;
          const [endX, endY] = bboxSelectEndPixel;

          const top = Math.min(startX, endX);
          const left = Math.min(startY, endY);
          const width = Math.abs(endY - startY);
          const height = Math.abs(endX - startX);

          selectedObjects =
            mapRef?.pickObjects({
              x: top,
              y: left,
              width,
              height,
            }) || [];
        }

        return {
          ...state,
          mapMode: MapMode.PAN,
          selectedObjects,
        };
      }
      return state;
    case ActionTypes.MAP_HOVER_EVENT:
      if (state.mapMode === MapMode.BBOX_SELECT_UPDATE) {
        return {
          ...state,
          bboxSelectEnd: action.data.coordinate,
          bboxSelectEndPixel: action.data.pixel,
        };
      }
      return state;
    case ActionTypes.TOGGLE_BBOX_SELECT_MODE:
      const nextMapMode =
        state.mapMode === MapMode.PAN ? MapMode.BBOX_SELECT_START : MapMode.PAN;

      // Clear bbox selection if we are starting a new selection
      if (nextMapMode === MapMode.BBOX_SELECT_START) {
        return {
          ...state,
          mapMode: nextMapMode,
          bboxSelectStart: undefined,
          bboxSelectEnd: undefined,
        };
      }

      return {
        ...state,
        mapMode: nextMapMode,
      };
    default:
      return state;
  }
};

const isLoggingEnabled = true;

export const reducer = isLoggingEnabled ? logReducer(baseReducer) : baseReducer;

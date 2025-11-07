import { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import { create } from "zustand";

interface AppState {
  highlightedFeature: GeoArrowPickingInfo | undefined;
  setHighlightedFeature: (feature: GeoArrowPickingInfo | undefined) => void;
  bboxSelectStart: number[] | undefined;
  bboxSelectEnd: number[] | undefined;
  isDrawingBbox: boolean;
  startBboxSelection: () => void;
  cancelBboxSelection: () => void;
  clearBboxSelection: () => void;
  setBboxStart: (coordinate: number[]) => void;
  setBboxEnd: (coordinate: number[]) => void;
  setBboxHover: (coordinate: number[]) => void;
}

export const useStore = create<AppState>((set) => ({
  highlightedFeature: undefined,
  setHighlightedFeature: (feature) => set({ highlightedFeature: feature }),
  bboxSelectStart: undefined,
  bboxSelectEnd: undefined,
  isDrawingBbox: false,
  startBboxSelection: () =>
    set({
      isDrawingBbox: true,
      bboxSelectStart: undefined,
      bboxSelectEnd: undefined,
    }),
  cancelBboxSelection: () =>
    set({
      isDrawingBbox: false,
      bboxSelectStart: undefined,
      bboxSelectEnd: undefined,
    }),
  clearBboxSelection: () =>
    set({ bboxSelectStart: undefined, bboxSelectEnd: undefined }),
  setBboxStart: (coordinate) => set({ bboxSelectStart: coordinate }),
  setBboxEnd: (coordinate) =>
    set((state) => {
      // Only finish drawing if a start point has been set
      if (state.bboxSelectStart) {
        return { bboxSelectEnd: coordinate, isDrawingBbox: false };
      }
      return {};
    }),
  setBboxHover: (coordinate) =>
    set((state) => {
      // Only update hover if we're drawing and have a start point
      if (state.isDrawingBbox && state.bboxSelectStart) {
        return { bboxSelectEnd: coordinate };
      }
      return {};
    }),
}));

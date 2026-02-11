/**
 * Client-side UI state management with Zustand.
 *
 * Manages ephemeral UI state that never syncs with Python. For Python-synced state,
 * use Backbone models via `useViewStateDebounced()` from `./python-sync.ts`.
 */
import type { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import { create } from "zustand";

/** Shape of the client-side UI state. All properties are UI-only. */
interface AppState {
  /** Feature currently highlighted by hover or click interaction */
  highlightedFeature: GeoArrowPickingInfo | undefined;
  /** Update the highlighted feature */
  setHighlightedFeature: (feature: GeoArrowPickingInfo | undefined) => void;

  /** Start coordinate for bounding box selection [lng, lat] */
  bboxSelectStart: number[] | undefined;
  /** End coordinate for bounding box selection [lng, lat] */
  bboxSelectEnd: number[] | undefined;
  /** Whether user is currently drawing a bounding box */
  isDrawingBbox: boolean;

  /** Actions for bounding box selection */
  startBboxSelection: () => void;
  cancelBboxSelection: () => void;
  clearBboxSelection: () => void;
  setBboxStart: (coordinate: number[]) => void;
  setBboxEnd: (coordinate: number[]) => void;
  setBboxHover: (coordinate: number[]) => void;
}

export const useStore = create<AppState>((set) => ({
  // Feature highlighting
  highlightedFeature: undefined,
  setHighlightedFeature: (feature) => set({ highlightedFeature: feature }),

  // Bounding box selection state
  bboxSelectStart: undefined,
  bboxSelectEnd: undefined,
  isDrawingBbox: false,

  // Bounding box actions
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
      // Complete selection only if we have a start point
      if (state.bboxSelectStart) {
        return { bboxSelectEnd: coordinate, isDrawingBbox: false };
      }
      return {};
    }),
  setBboxHover: (coordinate) =>
    set((state) => {
      // Show preview while drawing
      if (state.isDrawingBbox && state.bboxSelectStart) {
        return { bboxSelectEnd: coordinate };
      }
      return {};
    }),
}));

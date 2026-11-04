import type { IWidgetManager } from "@jupyter-widgets/base";
import { useEffect, useState } from "react";

import { MaplibreBasemapModel } from "../model/basemap.js";
import { loadModel } from "../model/initialize.js";

/**
 * Whether a map's basemap is ready to render
 *
 * - `loading`: the basemap model hasn't loaded yet
 * - `none`: render without a basemap, because the map has none or its model
 *   failed to load
 * - `loaded`: the basemap model is ready
 *
 * Changing the basemap keeps the current state until the new model loads.
 */
export type BasemapState =
  | { type: "loading" }
  | { type: "none" }
  | { type: "loaded"; basemap: MaplibreBasemapModel };

/**
 * Hook to manage basemap state loading and initialization
 *
 * @param basemapModelId - The ID of the basemap model to load
 * @param widgetManager - The Jupyter widget manager
 * @param updateStateCallback - Callback to trigger re-renders
 * @returns The basemap's loading state
 */
export function useBasemapState(
  basemapModelId: string | null,
  widgetManager: IWidgetManager,
  updateStateCallback: () => void,
): BasemapState {
  const [basemapState, setBasemapState] = useState<BasemapState>(() =>
    basemapModelId ? { type: "loading" } : { type: "none" },
  );

  useEffect(() => {
    const loadBasemap = async () => {
      try {
        if (!basemapModelId) {
          setBasemapState({ type: "none" });
          return;
        }

        const basemapModel = await loadModel(widgetManager, basemapModelId);
        const basemap = new MaplibreBasemapModel(
          basemapModel,
          updateStateCallback,
        );
        setBasemapState({ type: "loaded", basemap });
      } catch (error) {
        console.error("Error loading basemap model:", error);
        setBasemapState({ type: "none" });
      }
    };

    loadBasemap();
  }, [basemapModelId, updateStateCallback, widgetManager]);

  return basemapState;
}

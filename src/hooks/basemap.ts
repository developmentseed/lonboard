import type { IWidgetManager } from "@jupyter-widgets/base";
import { useEffect, useState } from "react";

import { MaplibreBasemapModel } from "../model/basemap.js";
import { loadModel } from "../model/initialize.js";

/**
 * Hook to manage basemap state loading and initialization
 *
 * @param basemapModelId - The ID of the basemap model to load
 * @param widgetManager - The Jupyter widget manager
 * @param updateStateCallback - Callback to trigger re-renders
 * @returns The initialized basemap model or null
 */
export function useBasemapState(
  basemapModelId: string | null,
  widgetManager: IWidgetManager,
  updateStateCallback: () => void,
): MaplibreBasemapModel | null {
  const [basemapState, setBasemapState] = useState<MaplibreBasemapModel | null>(
    null,
  );

  useEffect(() => {
    const loadBasemap = async () => {
      try {
        if (!basemapModelId) {
          setBasemapState(null);
          return;
        }

        const basemapModel = await loadModel(widgetManager, basemapModelId);
        const basemap = new MaplibreBasemapModel(
          basemapModel,
          updateStateCallback,
        );
        setBasemapState(basemap);
      } catch (error) {
        console.error("Error loading basemap model:", error);
      }
    };

    loadBasemap();
  }, [basemapModelId, updateStateCallback, widgetManager]);

  return basemapState;
}

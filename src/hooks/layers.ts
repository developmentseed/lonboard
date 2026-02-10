import type { Layer } from "@deck.gl/core";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import { useEffect, useState } from "react";
import type { BaseLayerModel } from "../model/index.js";
import { initializeChildModels, initializeLayer } from "../model/index.js";

/**
 * Hook to manage layers state loading and initialization
 *
 * @param layerIds - Array of layer model IDs to load
 * @param widgetManager - The Jupyter widget manager
 * @param updateStateCallback - Callback to trigger re-renders
 * @param bboxSelectBounds - Bounding box selection bounds to set on the model
 * @param isDrawingBBoxSelection - Whether currently drawing a bbox selection
 * @param model - The parent widget model
 * @returns Array of deck.gl layers ready to render
 */
export function useLayersState(
  layerIds: string[],
  widgetManager: IWidgetManager,
  updateStateCallback: () => void,
  bboxSelectBounds: number[] | null,
  isDrawingBBoxSelection: boolean,
  setSelectedBounds: (bounds: number[] | null) => void,
): Layer[] {
  const [layersState, setLayersState] = useState<
    Record<string, BaseLayerModel>
  >({});

  useEffect(() => {
    const loadAndUpdateLayers = async () => {
      try {
        const layerModels = await initializeChildModels<BaseLayerModel>(
          widgetManager,
          layerIds,
          layersState,
          async (model: WidgetModel) =>
            initializeLayer(model, updateStateCallback),
        );

        setLayersState(layerModels);

        if (!isDrawingBBoxSelection) {
          // Note: selected_bounds is a property of the **Map**. In the future,
          // when we use deck.gl to perform picking, we'll have
          // `selected_indices` as a property of each individual layer.
          setSelectedBounds(bboxSelectBounds);
        }
      } catch (error) {
        console.error("Error loading child models or setting bounds:", error);
      }
    };

    loadAndUpdateLayers();
  }, [layerIds, bboxSelectBounds, isDrawingBBoxSelection]);

  return Object.values(layersState).flatMap((layerModel) =>
    layerModel.render(),
  );
}

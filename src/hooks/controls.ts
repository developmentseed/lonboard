import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import { useEffect, useState } from "react";

import type { BaseMapControlModel } from "../model";
import { initializeChildModels } from "../model/index.js";
import { initializeControl } from "../model/map-control";

/**
 * Hook to manage map controls state
 */
export function useControlsState(
  controlsIds: string[],
  widgetManager: IWidgetManager,
  updateStateCallback: () => void,
): BaseMapControlModel[] {
  const [controlsState, setControlsState] = useState<
    Record<string, BaseMapControlModel>
  >({});

  useEffect(() => {
    const loadMapControls = async () => {
      try {
        const controlsModels = await initializeChildModels<BaseMapControlModel>(
          widgetManager,
          controlsIds,
          controlsState,
          async (model: WidgetModel) =>
            initializeControl(model, updateStateCallback),
        );

        setControlsState(controlsModels);
      } catch (error) {
        console.error("Error loading controls:", error);
      }
    };

    loadMapControls();
  }, [controlsIds]);

  return Object.values(controlsState);
}

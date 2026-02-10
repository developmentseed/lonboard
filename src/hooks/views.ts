import type { View } from "@deck.gl/core";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import { useEffect, useState } from "react";

import { initializeChildModels } from "../model/index.js";
import type { BaseViewModel } from "../model/view.js";
import { initializeView } from "../model/view.js";

/**
 * Hook to manage views state loading and initialization
 *
 * @param viewIds - View model ID(s) to load (single ID or array)
 * @param widgetManager - The Jupyter widget manager
 * @param updateStateCallback - Callback to trigger re-renders
 * @returns Array of deck.gl views or undefined (to use deck's default view)
 */
export function useViewsState(
  viewIds: string | string[] | null,
  widgetManager: IWidgetManager,
  updateStateCallback: () => void,
): View[] | undefined {
  const [viewsState, setViewsState] = useState<
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Record<string, BaseViewModel<any>>
  >({});

  useEffect(() => {
    const loadAndUpdateViews = async () => {
      try {
        if (!viewIds) {
          setViewsState({});
          return;
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const viewsModels = await initializeChildModels<BaseViewModel<any>>(
          widgetManager,
          typeof viewIds === "string" ? [viewIds] : viewIds,
          viewsState,
          async (model: WidgetModel) =>
            initializeView(model, updateStateCallback),
        );

        setViewsState(viewsModels);
      } catch (error) {
        console.error("Error loading child views:", error);
      }
    };

    loadAndUpdateViews();
  }, [viewIds, widgetManager, updateStateCallback, viewsState]);

  const views = Object.values(viewsState).map((viewModel) => viewModel.build());

  // When the user hasn't specified any views, we let deck.gl create
  // a default view, and so set undefined here.
  return views.length > 0 ? views : undefined;
}

import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";

/**
 * Load the child models of this model
 */
export async function loadChildModels(
  widget_manager: IWidgetManager,
  childLayerIds: string[],
): Promise<WidgetModel[]> {
  const promises: Promise<WidgetModel>[] = [];
  for (const childLayerId of childLayerIds) {
    promises.push(
      widget_manager.get_model(childLayerId.slice("IPY_MODEL_".length)),
    );
  }
  return await Promise.all(promises);
}

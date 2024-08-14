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

/** Check for null and undefined */
// https://stackoverflow.com/a/52097445
export function isDefined<T>(value: T | undefined | null): value is T {
  return value !== undefined && value !== null;
}

export function makePolygon(pt1: number[], pt2: number[]) {
  return [pt1, [pt1[0], pt2[1]], pt2, [pt2[0], pt1[1]], pt1];
}

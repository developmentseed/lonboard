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

// From https://www.joshwcomeau.com/snippets/javascript/debounce/
export const debounce = (callback: (args) => void, wait: number) => {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      callback.apply(null, args);
    }, wait);
  };
};

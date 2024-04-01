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

// From https://gist.github.com/ca0v/73a31f57b397606c9813472f7493a940
export function debounce<T extends Function>(cb: T, wait = 20) {
  let h: ReturnType<typeof setTimeout> | undefined;
  let callable = (...args: any) => {
    clearTimeout(h);
    h = setTimeout(() => cb(...args), wait);
  };
  return <T>(<any>callable);
}

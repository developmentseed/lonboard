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

// From https://gist.github.com/ca0v/73a31f57b397606c9813472f7493a940
export function debounce<T extends Function>(cb: T, wait = 20) {
  let h: ReturnType<typeof setTimeout> | undefined;
  let callable = (...args: any) => {
    clearTimeout(h);
    h = setTimeout(() => cb(...args), wait);
  };
  return <T>(<any>callable);
}

/**
 * Rate limit a function.
 *
 * @param cb function to rate limit
 * @param limit number of milliseconds to wait between calls
 * @returns the rate limited function
 */
export function rateLimit<T extends (...args: any[]) => void>(
  cb: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let lastCall = 0;

  return function (...args: Parameters<T>): void {
    const now = Date.now();

    if (now - lastCall >= limit) {
      lastCall = now;
      cb(...args);
    }
  };
}

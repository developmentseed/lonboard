/**
 * Python ↔ JavaScript state synchronization via Jupyter widgets.
 *
 * Provides hooks for state that requires bidirectional synchronization with Python
 * through Backbone models. Use this for data that Python needs to know about.
 */
import { useModel } from "@anywidget/react";
import type { AnyModel } from "@anywidget/types";
import debounce from "lodash.debounce";
import * as React from "react";

/** Debounce save operations to prevent WebSocket flooding (300ms delay) */
const debouncedModelSaveChanges = debounce((model: AnyModel) => {
  model.save_changes();
}, 300);

/**
 * Bidirectional state sync with Python using debounced updates.
 *
 * Python → JS: Immediate updates when Python changes the value
 * JS → Python: Debounced updates (300ms) to prevent flooding WebSocket
 *
 * @template T - Type of the state value
 * @param key - Model attribute name to sync (e.g., "view_state")
 * @returns [value, setValue] - Current value and debounced setter
 *
 * @example
 * ```ts
 * // Sync camera view state with Python
 * const [viewState, setViewState] = useViewStateDebounced<MapViewState>("view_state");
 *
 * // Updates from Python appear immediately
 * // Updates to Python are debounced
 * setViewState({ longitude: -122.4, latitude: 37.8, zoom: 12 });
 * ```
 */
export function useViewStateDebounced<T>(key: string): [T, (value: T) => void] {
  const model = useModel();
  const [value, setValue] = React.useState(model.get(key));

  // Listen for Python → JS changes
  React.useEffect(() => {
    const callback = () => setValue(model.get(key));
    model.on(`change:${key}`, callback);
    return () => model.off(`change:${key}`, callback);
  }, [model, key]);

  // Return JS → Python debounced setter
  return [
    value,
    (newValue) => {
      model.set(key, newValue);
      debouncedModelSaveChanges(model);
    },
  ];
}

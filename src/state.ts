import { useModel } from "@anywidget/react";
import type { AnyModel } from "@anywidget/types";
import debounce from "lodash.debounce";
import * as React from "react";

const debouncedModelSaveChanges = debounce((model: AnyModel) => {
  model.save_changes();
}, 300);

// TODO: add a `wait` parameter here, instead of having it hard-coded?
export function useViewStateDebounced<T>(key: string): [T, (value: T) => void] {
  const model = useModel();
  const [value, setValue] = React.useState(model.get(key));
  React.useEffect(() => {
    const callback = () => {
      setValue(model.get(key));
    };
    model.on(`change:${key}`, callback);
    return () => model.off(`change:${key}`, callback);
  }, [model, key]);
  return [
    value,
    (value) => {
      model.set(key, value);
      // Note: I think this has to be defined outside of this function so that
      // you're calling debounce on the same function object?
      debouncedModelSaveChanges(model);
    },
  ];
}

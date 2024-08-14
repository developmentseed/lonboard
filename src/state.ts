import * as React from "react";
import { useModel } from "@anywidget/react";
import type { AnyModel } from "@anywidget/types";
import debounce from "lodash.debounce";

const debouncedModelSaveViewState = debounce((model: AnyModel) => {
  // TODO: this and below is hard-coded to the view_state model property!
  const viewState = model.get("view_state");

  // transitionInterpolator is sometimes a key in the view state while panning
  // This is a function object and so can't be serialized via JSON.
  //
  // In the future anywidget may support custom serializers for sending data
  // back from JS to Python. Until then, we need to clean the object ourselves.
  // Because this is in a debounce it shouldn't often mess with deck's internal
  // transition state it expects, because hopefully the transition will have
  // finished in the 300ms that the user has stopped panning.
  if ("transitionInterpolator" in viewState) {
    console.debug("Deleting transitionInterpolator!");
    delete viewState.transitionInterpolator;
    model.set("view_state", viewState);
  }

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
      debouncedModelSaveViewState(model);
    },
  ];
}

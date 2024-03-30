import * as React from "react";
import { useModel } from "@anywidget/react";
import { debounce } from "./util";

const debouncedModelSaveViewState = debounce((model) => {
  console.log("DEBOUNCED");
  const viewState = model.get("_view_state");

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
    model.set("_view_state", viewState);
  }

  model.save_changes();
}, 300);

export function useModelStateDebounced<T>(
  key: string,
  wait: number
): [T, (value: T) => void] {
  let model = useModel();
  let [value, setValue] = React.useState(model.get(key));
  React.useEffect(() => {
    let callback = () => {
      console.log("callback");
      console.log(model.get(key));
      setValue(model.get(key));
    };
    model.on(`change:${key}`, callback);
    console.log(`model on change view state`);
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
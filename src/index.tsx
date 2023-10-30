import * as React from "react";
import { useState, useEffect } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import type { Layer } from "@deck.gl/core/typed";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import {
  BaseGeoArrowModel,
  PathModel,
  ScatterplotModel,
  SolidPolygonModel,
} from "./model";
import { useParquetWasm } from "./parquet";
import { getTooltip } from "./tooltip";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

/**
 * Load the child models of this model
 */
async function loadChildModels(
  widget_manager: IWidgetManager,
  childLayerIds: string[]
): Promise<WidgetModel[]> {
  const promises: Promise<WidgetModel>[] = [];
  for (const childLayerId of childLayerIds) {
    promises.push(
      widget_manager.get_model(childLayerId.slice("IPY_MODEL_".length))
    );
  }
  return await Promise.all(promises);
}

function App() {
  let [parquetWasmReady] = useParquetWasm();
  let [initialViewState] = useModelState<DataView>("_initial_view_state");

  let [subModelState, setSubModelState] = useState<
    Record<string, BaseGeoArrowModel>
  >({});
  let model = useModel();
  let [childLayerIds] = useModelState<string[]>("layers");

  // Fake state just to get react to re-render when a model callback is called
  let [stateCounter, setStateCounter] = useState<Date>(new Date());

  useEffect(() => {
    if (!parquetWasmReady) {
      return;
    }

    const callback = async () => {
      if (!parquetWasmReady) {
        throw new Error("inside callback but parquetWasm not ready!");
      }

      const newSubModelState: Record<string, BaseGeoArrowModel> = {};
      const childModels = await loadChildModels(
        model.widget_manager,
        childLayerIds
      );

      for (let i = 0; i < childLayerIds.length; i++) {
        const childLayerId = childLayerIds[i];
        const childModel = childModels[i];

        // If the layer existed previously, copy its model without constructing
        // a new one
        if (childLayerId in subModelState) {
          // pop from old state
          newSubModelState[childLayerId] = subModelState[childLayerId];
          delete subModelState[childLayerId];
          continue;
        }

        const layerType = childModel.get("_layer_type");
        switch (layerType) {
          case "scatterplot":
            newSubModelState[childLayerId] = new ScatterplotModel(
              childModel,
              () => setStateCounter(new Date())
            );
            break;
          case "path":
            newSubModelState[childLayerId] = new PathModel(childModel, () =>
              setStateCounter(new Date())
            );
            break;
          case "solid-polygon":
            newSubModelState[childLayerId] = new SolidPolygonModel(
              childModel,
              () => setStateCounter(new Date())
            );
            break;
          default:
            console.error(`no layer supported for ${layerType}`);
            break;
        }
      }

      // finalize models that were deleted
      for (const previousChildModel of Object.values(subModelState)) {
        previousChildModel.finalize();
      }

      setSubModelState(newSubModelState);
    };
    callback().catch(console.error);
  }, [parquetWasmReady, childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  return (
    <div style={{ height: 500 }}>
      <DeckGL
        initialViewState={
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(initialViewState).includes(key)
          )
            ? initialViewState
            : DEFAULT_INITIAL_VIEW_STATE
        }
        controller={true}
        layers={layers}
        getTooltip={getTooltip}
        pickingRadius={10}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

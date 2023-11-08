import * as React from "react";
import { useState, useEffect } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import type { Layer } from "@deck.gl/core/typed";
import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseLayerModel, initializeLayer } from "./model";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import {
  ArcModel,
  BaseLayerModel,
  HeatmapModel,
  PathModel,
  ScatterplotModel,
  SolidPolygonModel,
} from "./model";
import { useParquetWasm } from "./parquet";
import { getTooltip } from "./tooltip";
import { loadChildModels } from "./util";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

async function getChildModelState(
  childModels: WidgetModel[],
  childLayerIds: string[],
  previousSubModelState: Record<string, BaseLayerModel>,
  setStateCounter: React.Dispatch<React.SetStateAction<Date>>
): Promise<Record<string, BaseLayerModel>> {
  const newSubModelState: Record<string, BaseLayerModel> = {};
  const updateStateCallback = () => setStateCounter(new Date());

  for (let i = 0; i < childLayerIds.length; i++) {
    const childLayerId = childLayerIds[i];
    const childModel = childModels[i];

    // If the layer existed previously, copy its model without constructing
    // a new one
    if (childLayerId in previousSubModelState) {
      // pop from old state
      newSubModelState[childLayerId] = previousSubModelState[childLayerId];
      delete previousSubModelState[childLayerId];
      continue;
    }

    const childLayer = await initializeLayer(childModel, updateStateCallback);
    newSubModelState[childLayerId] = childLayer;
  }

  // finalize models that were deleted
  for (const previousChildModel of Object.values(previousSubModelState)) {
    previousChildModel.finalize();
  }

  return newSubModelState;
}

function App() {
  let [parquetWasmReady] = useParquetWasm();
  let [initialViewState] = useModelState<DataView>("_initial_view_state");
  let [mapHeight] = useModelState<number>("_height");
  let [showTooltip] = useModelState<boolean>("show_tooltip");
  let [pickingRadius] = useModelState<number>("picking_radius");

  let [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
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

      const childModels = await loadChildModels(
        model.widget_manager,
        childLayerIds
      );
      const newSubModelState = await getChildModelState(
        childModels,
        childLayerIds,
        subModelState,
        setStateCounter
      );
      setSubModelState(newSubModelState);
    };
    callback().catch(console.error);
  }, [parquetWasmReady, childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  return (
    <div style={{ height: mapHeight || 500 }}>
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
        getTooltip={showTooltip && getTooltip}
        pickingRadius={pickingRadius}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

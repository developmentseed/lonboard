import * as React from "react";
import { useState, useEffect } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { MapViewState, Widget, type Layer } from "@deck.gl/core";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { initParquetWasm } from "./parquet.js";
import { getTooltip } from "./tooltip/index.js";
import { isDefined, loadChildModels } from "./util.js";
import { v4 as uuidv4 } from "uuid";
import { Message } from "./types.js";
import { flyTo } from "./actions/fly-to.js";
import { useViewStateDebounced } from "./state";
import { BaseDeckWidgetModel, initializeWidget } from "./model/deck-widget-models.js";
import './widget-style.css'

await initParquetWasm();

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const DEFAULT_MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

async function getChildModelState(
  childModels: WidgetModel[],
  childLayerIds: string[],
  previousSubModelState: Record<string, BaseLayerModel>,
  setStateCounter: React.Dispatch<React.SetStateAction<Date>>,
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

async function getDeckWidgetModelState(
  deckWidgetModels: WidgetModel[],
  deckWidgetIds: string[],
  previousSubModelState: Record<string, BaseDeckWidgetModel>,
  setStateCounter: React.Dispatch<React.SetStateAction<Date>>,
): Promise<Record<string, BaseDeckWidgetModel>> {
  const newDeckWidgetModelState: Record<string, BaseDeckWidgetModel> = {};
  const updateStateCallback = () => setStateCounter(new Date());

  for (let i = 0; i < deckWidgetIds.length; i++) {
    const deckWidgetId = deckWidgetIds[i];
    const deckWidgetModel = deckWidgetModels[i];

    // If the layer existed previously, copy its model without constructing
    // a new one
    if (deckWidgetId in previousSubModelState) {
      // pop from old state
      newDeckWidgetModelState[deckWidgetId] = previousSubModelState[deckWidgetId];
      delete previousSubModelState[deckWidgetId];
      continue;
    }

    const deckWidget = await initializeWidget(deckWidgetModel, updateStateCallback);
    newDeckWidgetModelState[deckWidgetId] = deckWidget;
  }

  // finalize models that were deleted
  for (const previousDeckWidgetModel of Object.values(previousSubModelState)) {
    previousDeckWidgetModel.finalize();
  }

  return newDeckWidgetModelState;
}

function App() {
  let model = useModel();

  let [mapStyle] = useModelState<string>("basemap_style");
  let [mapHeight] = useModelState<number>("height");
  let [mapWidth] = useModelState<number>("width");
  let [showTooltip] = useModelState<boolean>("show_tooltip");
  let [pickingRadius] = useModelState<number>("picking_radius");
  let [useDevicePixels] = useModelState<number | boolean>("use_device_pixels");
  let [parameters] = useModelState<object>("parameters");

  // initialViewState is the value of view_state on the Python side. This is
  // called `initial` here because it gets passed in to deck's
  // `initialViewState` param, as deck manages its own view state. Further
  // updates to `view_state` from Python are set on the deck `initialViewState`
  // property, which can set new camera state, as described here:
  // https://deck.gl/docs/developer-guide/interactivity
  //
  // `setViewState` is a debounced way to update the model and send view
  // state information back to Python.
  const [initialViewState, setViewState] =
    useViewStateDebounced<MapViewState>("view_state");

  // Handle custom messages
  model.on("msg:custom", (msg: Message, buffers) => {
    switch (msg.type) {
      case "fly-to":
        flyTo(msg, setViewState);
        break;

      default:
        break;
    }
  });

  const [mapId] = useState(uuidv4());

  let [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});

  let [deckWidgetState, setDeckWidgetState] = useState<
    Record<string, BaseDeckWidgetModel>
  >({});

  let [childLayerIds] = useModelState<string[]>("layers");
  let [deckWidgetIds] = useModelState<string[]>("deck_widgets");

  // Fake state just to get react to re-render when a model callback is called
  let [stateCounter, setStateCounter] = useState<Date>(new Date());

  useEffect(() => {
    const callback = async () => {
      const childModels = await loadChildModels(
        model.widget_manager,
        childLayerIds,
      );
      const newSubModelState = await getChildModelState(
        childModels,
        childLayerIds,
        subModelState,
        setStateCounter,
      );
      setSubModelState(newSubModelState);

      const deckWidgetModels = await loadChildModels(
        model.widget_manager,
        deckWidgetIds,
      );
      const newDeckWidgetState = await getDeckWidgetModelState(
        deckWidgetModels,
        deckWidgetIds,
        deckWidgetState,
        setStateCounter,
      );
      setDeckWidgetState(newDeckWidgetState);

    };
    callback().catch(console.error);
  }, [childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  const deckWidgets: Widget[] = [];
  for (const deckWidget of Object.values(deckWidgetState)) {
    deckWidgets.push(deckWidget.render());
  }

  // This hook checks if the map container parent has a height set, which is
  // needed to make the map fill the parent container.
  useEffect(() => {
    if (mapHeight) return;

    const mapContainer = document.getElementById(`map-${mapId}`);
    const mapContainerParent = mapContainer?.parentElement;

    if (mapContainerParent) {
      // Compute the actual style considering stylesheets, inline styles, and browser default styles
      const parentStyle = window.getComputedStyle(mapContainerParent);

      // Check if the height is not already set
      if (!parentStyle.height || parentStyle.height === "0px") {
        // Set the height to 100% and min-height
        mapContainerParent.style.height = "100%";
        mapContainerParent.style.minHeight = "500px";
      }
    }
  }, []);

  return (
    <div id={`map-${mapId}`} style={{ height: mapHeight || "100%", width: mapWidth || "100%" }}>
      <DeckGL
        initialViewState={
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(initialViewState).includes(key),
          )
            ? initialViewState
            : DEFAULT_INITIAL_VIEW_STATE
        }
        controller={true}
        layers={layers}
        widgets={deckWidgets}
        width={mapWidth}
        height={mapHeight}
        // @ts-expect-error
        getTooltip={showTooltip && getTooltip}
        pickingRadius={pickingRadius}
        useDevicePixels={isDefined(useDevicePixels) ? useDevicePixels : true}
        // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
        _typedArrayManagerProps={{
          overAlloc: 1,
          poolSize: 0,
        }}
        parameters={parameters || {}}
      >
        <Map mapStyle={mapStyle || DEFAULT_MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(App),
};

export default module;

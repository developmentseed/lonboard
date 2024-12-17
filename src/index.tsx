import * as React from "react";
import { useEffect, useCallback, useState } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { MapViewState, PickingInfo, type Layer } from "@deck.gl/core";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { initParquetWasm } from "./parquet.js";
import { isDefined, loadChildModels } from "./util.js";
import { v4 as uuidv4 } from "uuid";
import { Message } from "./types.js";
import { flyTo } from "./actions/fly-to.js";
import { useViewStateDebounced } from "./state";

import { MachineContext, MachineProvider } from "./xstate";
import * as selectors from "./xstate/selectors";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import { NextUIProvider } from "@nextui-org/react";
import Toolbar from "./toolbar.js";
import throttle from "lodash.throttle";
import SidePanel from "./sidepanel/index";

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

function App() {
  const actorRef = MachineContext.useActorRef();
  const isDrawingBBoxSelection = MachineContext.useSelector(
    selectors.isDrawingBBoxSelection,
  );
  const isOnMapHoverEventEnabled = MachineContext.useSelector(
    selectors.isOnMapHoverEventEnabled,
  );

  const highlightedFeature = MachineContext.useSelector(
    (s) => s.context.highlightedFeature,
  );

  const bboxSelectPolygonLayer = MachineContext.useSelector(
    selectors.getBboxSelectPolygonLayer,
  );
  const bboxSelectBounds = MachineContext.useSelector(
    selectors.getBboxSelectBounds,
  );

  const [justClicked, setJustClicked] = useState<boolean>(false);

  const model = useModel();

  const [mapStyle] = useModelState<string>("basemap_style");
  const [mapHeight] = useModelState<number>("_height");
  const [showTooltip] = useModelState<boolean>("show_tooltip");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [useDevicePixels] = useModelState<number | boolean>(
    "use_device_pixels",
  );
  const [parameters] = useModelState<object>("parameters");
  const [customAttribution] = useModelState<string>("custom_attribution");

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
  model.on("msg:custom", (msg: Message) => {
    switch (msg.type) {
      case "fly-to":
        flyTo(msg, setViewState);
        break;

      default:
        break;
    }
  });

  const [mapId] = useState(uuidv4());
  const [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});

  const [childLayerIds] = useModelState<string[]>("layers");

  // Fake state just to get react to re-render when a model callback is called
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [stateCounter, setStateCounter] = useState<Date>(new Date());

  useEffect(() => {
    const loadAndUpdateLayers = async () => {
      try {
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

        if (!isDrawingBBoxSelection) {
          // Note: selected_bounds is a property of the **Map**. In the future,
          // when we use deck.gl to perform picking, we'll have
          // `selected_indices` as a property of each individual layer.
          model.set("selected_bounds", bboxSelectBounds);
          model.save_changes();
          // childModels.forEach((layer) => {
          //   layer.set("selected_bounds", bboxSelectBounds);
          //   layer.save_changes();
          // });
        }
      } catch (error) {
        console.error("Error loading child models or setting bounds:", error);
      }
    };

    loadAndUpdateLayers();
  }, [childLayerIds, bboxSelectBounds, isDrawingBBoxSelection]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  const onMapClickHandler = useCallback((info: PickingInfo) => {
    // We added this flag to prevent the hover event from firing after a
    // click event.
    if (typeof info.coordinate !== "undefined") {
      if (model.get("_has_click_handlers")) {
        model.send({ kind: "on-click", coordinate: info.coordinate });
      }
    }
    setJustClicked(true);
    actorRef.send({
      type: "Map click event",
      data: info,
    });
    setTimeout(() => {
      setJustClicked(false);
    }, 100);
  }, []);

  const onMapHoverHandler = useCallback(
    throttle(
      (info: PickingInfo) =>
        isOnMapHoverEventEnabled &&
        !justClicked &&
        actorRef.send({
          type: "Map hover event",
          data: info,
        }),
      100,
    ),
    [isOnMapHoverEventEnabled, justClicked],
  );

  return (
    <div
      id={`map-${mapId}`}
      className="flex"
      style={{ height: mapHeight ? `${mapHeight}px` : "24rem" }}
    >
      <Toolbar />

      {showTooltip && highlightedFeature && (
        <SidePanel
          info={highlightedFeature}
          onClose={() => actorRef.send({ type: "Close side panel" })}
        />
      )}
      <div className="bg-red-800 h-full w-full relative">
        <DeckGL
          style={{ width: "100%", height: "100%" }}
          initialViewState={
            ["longitude", "latitude", "zoom"].every((key) =>
              Object.keys(initialViewState).includes(key),
            )
              ? initialViewState
              : DEFAULT_INITIAL_VIEW_STATE
          }
          controller={true}
          layers={
            bboxSelectPolygonLayer
              ? layers.concat(bboxSelectPolygonLayer)
              : layers
          }
          getCursor={() => (isDrawingBBoxSelection ? "crosshair" : "grab")}
          pickingRadius={pickingRadius}
          onClick={onMapClickHandler}
          onHover={onMapHoverHandler}
          useDevicePixels={isDefined(useDevicePixels) ? useDevicePixels : true}
          // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
          _typedArrayManagerProps={{
            overAlloc: 1,
            poolSize: 0,
          }}
          onViewStateChange={(event) => {
            const { viewState } = event;

            // This condition is necessary to confirm that the viewState is
            // of type MapViewState.
            if ("latitude" in viewState) {
              const { longitude, latitude, zoom, pitch, bearing } = viewState;
              setViewState({
                longitude,
                latitude,
                zoom,
                pitch,
                bearing,
              });
            }
          }}
          parameters={parameters || {}}
        >
          <Map
            mapStyle={mapStyle || DEFAULT_MAP_STYLE}
            customAttribution={customAttribution}
          ></Map>
        </DeckGL>
      </div>
    </div>
  );
}

const WrappedApp = () => (
  <NextUIProvider>
    <MachineProvider>
      <App />
    </MachineProvider>
  </NextUIProvider>
);

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(WrappedApp),
};

export default module;

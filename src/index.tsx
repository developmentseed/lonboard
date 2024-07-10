import React, { useCallback, useReducer, useRef } from "react";
import { useState, useEffect } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import Map from "react-map-gl/maplibre";
import DeckGL, { DeckGLRef } from "@deck.gl/react/typed";
import { MapViewState, PickingInfo, type Layer } from "@deck.gl/core/typed";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { initParquetWasm } from "./parquet.js";
import { getTooltip } from "./tooltip/index.js";
import { isDefined, loadChildModels, rateLimit } from "./util.js";
import { v4 as uuidv4 } from "uuid";
import { Message } from "./types.js";
import { flyTo } from "./actions/fly-to.js";
import { useViewStateDebounced } from "./state";
import * as selectors from "./reducer/selectors";

import "maplibre-gl/dist/maplibre-gl.css";

import {
  ActionTypes,
  baseInitialState,
  MapMode,
  reducer,
} from "./reducer/index.js";

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
  const [state, dispatch] = useReducer(reducer, baseInitialState);

  const isMapHoverEnabled = selectors.isMapHoverEnabled(state);
  const isMapClickEnabled = selectors.isMapClickEnabled(state);
  const [justClicked, setJustClicked] = useState<boolean>(false);
  const bboxSelectPolygonLayer = selectors.bboxSelectPolygonLayer(state);

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
  const mapRef = useRef<DeckGLRef>(null);
  const [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});

  const [childLayerIds] = useModelState<string[]>("layers");

  // Fake state just to get react to re-render when a model callback is called
  const [stateCounter, setStateCounter] = useState<Date>(new Date());

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
    };
    callback().catch(console.error);
  }, [childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
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

  const onMapClickHandler = useCallback(
    (info: PickingInfo) => {
      if (isMapClickEnabled) {
        // We added this flag to prevent the hover event from firing after a
        // click event.
        setJustClicked(true);
        dispatch({ type: ActionTypes.MAP_CLICK_EVENT, data: info });
        setTimeout(() => {
          setJustClicked(false);
        }, 100);
      }
    },
    [isMapClickEnabled],
  );

  const onMapHoverHandler = useCallback(
    rateLimit(
      (info: PickingInfo) =>
        isMapHoverEnabled &&
        !justClicked &&
        dispatch({ type: ActionTypes.MAP_HOVER_EVENT, data: info }),
      100,
    ),
    [isMapHoverEnabled, justClicked],
  );

  return (
    <div id={`map-${mapId}`} style={{ height: mapHeight || "100%" }}>
      <div
        style={{
          position: "absolute",
          top: "2px",
          right: "2px",
          backgroundColor: "#fff",
          padding: "2px",
          zIndex: "1000",
          height: "12px",
        }}
        onClick={() => {
          dispatch({ type: ActionTypes.TOGGLE_BBOX_SELECT_MODE });
        }}
      >
        {state.mapMode === MapMode.BBOX_SELECT_START
          ? "Bbox select mode"
          : "Pan mode"}
      </div>
      <DeckGL
        initialViewState={
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(initialViewState).includes(key),
          )
            ? initialViewState
            : DEFAULT_INITIAL_VIEW_STATE
        }
        controller={true}
        layers={layers.concat(bboxSelectPolygonLayer)}
        // @ts-expect-error
        getTooltip={showTooltip && state.mapMode === MapMode.PAN && getTooltip}
        pickingRadius={pickingRadius}
        onHover={onMapHoverHandler}
        onClick={onMapClickHandler}
        ref={mapRef}
        useDevicePixels={isDefined(useDevicePixels) ? useDevicePixels : true}
        // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
        _typedArrayManagerProps={{
          overAlloc: 1,
          poolSize: 0,
        }}
        onLoad={() => {
          if (mapRef.current) {
            dispatch({
              type: ActionTypes.SET_MAP_REF,
              data: mapRef.current,
            });
          }
        }}
        onViewStateChange={(event) => {
          const { viewState } = event;
          const { longitude, latitude, zoom, pitch, bearing } = viewState;
          setViewState({
            longitude,
            latitude,
            zoom,
            pitch,
            bearing,
          });
        }}
        parameters={parameters || {}}
      >
        <Map
          mapStyle={mapStyle || DEFAULT_MAP_STYLE}
          customAttribution={customAttribution}
        ></Map>
      </DeckGL>
    </div>
  );
}

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(App),
};

export default module;

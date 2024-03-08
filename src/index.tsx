import * as React from "react";
import { useState, useEffect, useMemo } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import type { Layer, PickingInfo } from "@deck.gl/core/typed";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { initParquetWasm } from "./parquet.js";
import { getTooltip } from "./tooltip/index.js";
import { loadChildModels } from "./util.js";
import { v4 as uuidv4 } from "uuid";

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
  let [initialViewState] = useModelState<DataView>("_initial_view_state");
  let [mapStyle] = useModelState<string>("basemap_style");
  let [mapHeight] = useModelState<number>("_height");
  let [showTooltip] = useModelState<boolean>("show_tooltip");
  let [pickingRadius] = useModelState<number>("picking_radius");
  const [mapId] = useState(uuidv4());

  let [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});
  let model = useModel();
  let [childLayerIds] = useModelState<string[]>("layers");

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

  const [selectionStart, setSelectionStart] = useState<
    undefined | [[number, number], number[] | undefined]
  >();
  const [selectionEnd, setSelectionEnd] = useState<
    undefined | [[number, number], number[] | undefined]
  >();

  function onClick(info: PickingInfo) {
    if (selectionEnd !== undefined) {
      setSelectionStart(undefined);
      setSelectionEnd(undefined);
    } else if (selectionStart !== undefined && selectionEnd === undefined) {
      setSelectionEnd([[info.x, info.y], info.coordinate]);
    } else {
      setSelectionStart([[info.x, info.y], info.coordinate]);
      setSelectionEnd(undefined);
    }
  }

  const selectionIndicator = useMemo(() => {
    // TODO: Recalculate this on layout change
    // TODO: Recalculate this on deckgl viewport change -- should be geo references
    if (selectionStart && selectionEnd) {
      const width = Math.abs(selectionEnd[0][0] - selectionStart[0][0]);
      const height = Math.abs(selectionEnd[0][1] - selectionStart[0][1]);
      const left = Math.min(selectionStart[0][0], selectionEnd[0][0]);
      const top = Math.min(selectionStart[0][1], selectionEnd[0][1]);

      console.log(
        `Selection made: left=${left} top=${top} width=${width} height=${height}`,
      );
      console.log(`Map coords: ${selectionStart[1]} ${selectionEnd[1]}`);

      return (
        <div
          style={{
            position: "relative",
            left,
            top,
            width,
            height,
            // show selection area
            borderColor: "black",
            borderWidth: "1px",
            backgroundColor: "rgba(0,0,1,0.5)",
          }}
        />
      );
    } else if (selectionStart) {
      return (
        <div
          style={{
            position: "relative",
            left: selectionStart[0][0],
            top: selectionStart[0][1],
            width: 5,
            height: 5,
            // show selection area
            borderColor: "black",
            borderWidth: "1px",
            backgroundColor: "rgba(0,0,1,0.5)",
            // render as a circle
            borderRadius: "2px",
          }}
        />
      );
    } else {
      return undefined;
    }
  }, [selectionStart, selectionEnd]);

  return (
    <div id={`map-${mapId}`} style={{ height: mapHeight || "100%" }}>
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
        // @ts-expect-error
        getTooltip={showTooltip && getTooltip}
        pickingRadius={pickingRadius}
        onClick={onClick}
      >
        <Map mapStyle={mapStyle || DEFAULT_MAP_STYLE} />
        <div
          style={{
            height: "100%",
            width: "100%",
          }}
        >
          {selectionIndicator}
        </div>
      </DeckGL>
    </div>
  );
}

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(App),
};

export default module;

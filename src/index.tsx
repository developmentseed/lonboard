import * as React from "react";
import { useState, useEffect, useMemo, useRef } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import Map from "react-map-gl/maplibre";
import DeckGL, { DeckGLRef } from "@deck.gl/react/typed";
import { PolygonLayer, ScatterplotLayer } from "@deck.gl/layers/typed";
import type { PickingInfo } from "@deck.gl/core/typed";
import { MapViewState, type Layer } from "@deck.gl/core/typed";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { initParquetWasm } from "./parquet.js";
import { getTooltip } from "./tooltip/index.js";
import { getPolygon, isDefined, loadChildModels } from "./util.js";
import { v4 as uuidv4 } from "uuid";
import { Message } from "./types.js";
import { flyTo } from "./actions/fly-to.js";

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
  const model = useModel();

  const [pythonInitialViewState] = useModelState<MapViewState>(
    "_initial_view_state",
  );
  const [mapStyle] = useModelState<string>("basemap_style");
  const [mapHeight] = useModelState<number>("_height");
  const [showTooltip] = useModelState<boolean>("show_tooltip");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [boundsModel, setBoundsModel] =
    useModelState<Array<number>>("selected_bounds");
  const [selectionMode, setSelectionMode] = useState<boolean | string>(false);
  const [selectionObjectCount, setSelectionObjectCount] = useState<
    boolean | number
  >(false);
  const [hoverBBoxLayer, setHoverBBoxLayer] = useState<any>(false);
  const [useDevicePixels] = useModelState<number | boolean>(
    "use_device_pixels",
  );
  const [parameters] = useModelState<object>("parameters");

  const [initialViewState, setInitialViewState] = useState(
    pythonInitialViewState,
  );

  // Handle custom messages
  model.on("msg:custom", (msg: Message, buffers) => {
    switch (msg.type) {
      case "fly-to":
        flyTo(msg, setInitialViewState);
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

  // State is an array of: [screen coordinates, geographic coordinates]
  const [selectionStart, setSelectionStart] = useState<
    undefined | [[number, number], number[] | undefined]
  >();
  const [selectionEnd, setSelectionEnd] = useState<
    undefined | [[number, number], number[] | undefined]
  >();

  function onSelectClick() {
    if (!selectionMode) {
      setSelectionMode("selecting");
    }
    if (selectionMode === "selected") {
      setSelectionMode(false);
      setSelectionStart(undefined);
      setSelectionEnd(undefined);
    }
  }

  function onMapClick(info: PickingInfo) {
    if (!selectionMode || selectionMode === "selected") return;
    if (selectionStart !== undefined && selectionEnd === undefined) {
      setSelectionEnd([[info.x, info.y], info.coordinate]);
      const pt1 = selectionStart[0];
      const pt2 = [info.x, info.y];

      const width = Math.abs(pt2[0] - pt1[0]);
      const height = Math.abs(pt2[1] - pt1[1]);
      const left = Math.min(pt1[0], pt2[0]);
      const top = Math.min(pt1[1], pt2[1]);
      const selectedObjects = mapRef.current?.pickObjects({
        x: left,
        y: top,
        width,
        height,
      });
      setSelectionMode("selected");
      setHoverBBoxLayer(false);
      setSelectionObjectCount(selectedObjects ? selectedObjects.length : 0);

      // set this to what Shapely uses to represent Bounds
      setBoundsModel([
        Math.min(pt1[0], pt2[0]),
        Math.min(pt1[1], pt2[1]),
        Math.max(pt1[0], pt2[0]),
        Math.max(pt1[1], pt2[1]),
      ]);
    } else {
      setSelectionStart([[info.x, info.y], info.coordinate]);
      setSelectionEnd(undefined);
    }
  }

  function onMapHover(hoverInfo: PickingInfo) {
    if (selectionMode !== "selecting") return;
    const hoverCoords = hoverInfo.coordinate;
    if (selectionStart && hoverCoords) {
      const pt1 = selectionStart[1];
      const pt2 = hoverCoords;
      if (!pt1 || !pt2) return;
      const data = [
        {
          polygon: getPolygon(pt1, pt2),
        },
      ];
      const bboxLayer = new PolygonLayer({
        id: "selection-layer",
        data,
        filled: true,
        getFillColor: [0, 0, 0, 50],
        stroked: true,
        getLineWidth: 2,
        lineWidthUnits: "pixels",
        getPolygon: (d) => d.polygon,
      });
      console.log(bboxLayer);
      setHoverBBoxLayer(bboxLayer);
    }
    return;
  }

  const selectionIndicator = useMemo(() => {
    if (!selectionMode) return undefined;
    if (selectionStart && selectionEnd) {
      const pt1 = selectionStart[1];
      const pt2 = selectionEnd[1];
      if (!pt1 || !pt2) return undefined;
      const data = [
        {
          polygon: getPolygon(pt1, pt2),
        },
      ];
      return new PolygonLayer({
        id: "selection-layer",
        data,
        filled: true,
        getFillColor: [0, 0, 0, 30],
        stroked: true,
        getLineWidth: 2,
        lineWidthUnits: "pixels",
        getPolygon: (d) => d.polygon,
      });
    } else {
      return undefined;
    }
  }, [selectionStart, selectionEnd, selectionMode]);

  if (selectionIndicator) {
    layers.push(selectionIndicator);
  }

  if (hoverBBoxLayer) {
    layers.push(hoverBBoxLayer);
  }

  return (
    <div id={`map-${mapId}`} style={{ height: "100%" }}>
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
        onClick={onSelectClick}
      >
        {!selectionMode ? "Click to start selecting" : ""}
        {selectionMode === "selecting"
          ? "Click two points on map to draw bounding box"
          : ""}
        {selectionMode === "selected"
          ? `${selectionObjectCount} objects selected. Click to Unselect.`
          : ""}
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
        layers={layers}
        // @ts-expect-error
        getTooltip={showTooltip && getTooltip}
        pickingRadius={pickingRadius}
        onClick={onMapClick}
        onHover={onMapHover}
        ref={mapRef}
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

import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import { GeoArrowPathLayer } from "@geoarrow/deck.gl-layers";
import { useParquetWasm } from "./parquet";
import { useAccessorState, useTableBufferState } from "./accessor";
import { useModelStateDebounced } from "./state";
import { MapViewState } from "@deck.gl/core/typed";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

function App() {
  const [wasmReady] = useParquetWasm();
  let [viewState, setViewState] = useModelStateDebounced<MapViewState>(
    "_view_state",
    300
  );
  console.log(viewState);

  let [dataRaw] = useModelState<DataView[]>("table");
  let [widthUnits] = useModelState("width_units");
  let [widthScale] = useModelState("width_scale");
  let [widthMinPixels] = useModelState("width_min_pixels");
  let [widthMaxPixels] = useModelState("width_max_pixels");
  let [jointRounded] = useModelState("joint_rounded");
  let [capRounded] = useModelState("cap_rounded");
  let [miterLimit] = useModelState("miter_limit");
  let [billboard] = useModelState("billboard");
  let [getColorRaw] = useModelState("get_color");
  let [getWidthRaw] = useModelState("get_width");

  const [dataTable] = useTableBufferState(wasmReady, dataRaw);
  const [getColor] = useAccessorState(wasmReady, getColorRaw);
  const [getWidth] = useAccessorState(wasmReady, getWidthRaw);

  const layers = [];
  if (dataTable) {
    // @ts-ignore
    const layer = new GeoArrowPathLayer({
      id: "geoarrow-path",
      data: dataTable,

      ...(widthUnits && { widthUnits }),
      ...(widthScale && { widthScale }),
      ...(widthMinPixels && { widthMinPixels }),
      ...(widthMaxPixels && { widthMaxPixels }),
      ...(jointRounded && { jointRounded }),
      ...(capRounded && { capRounded }),
      ...(miterLimit && { miterLimit }),
      ...(billboard && { billboard }),
      ...(getColor && { getColor }),
      ...(getWidth && { getWidth }),
    });
    layers.push(layer);
  }

  return (
    <div style={{ height: 500 }}>
      <DeckGL
        controller={true}
        layers={layers}
        viewState={
          Object.keys(viewState).length === 0
            ? DEFAULT_INITIAL_VIEW_STATE
            : viewState
        }
        onViewStateChange={(event) => {
          // @ts-expect-error here viewState is typed as Record<string, any>
          setViewState(event.viewState);
        }}
        // ContextProvider={MapContext.Provider}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

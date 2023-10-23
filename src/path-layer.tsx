import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import { GeoArrowPathLayer } from "@geoarrow/deck.gl-layers";
import { useParquetWasm } from "./parquet";
import { useAccessorState, useTableBufferState } from "./accessor";

import "maplibre-gl/dist/maplibre-gl.css";

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

  let [viewState] = useModelState<DataView>("_initial_view_state");
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
        initialViewState={
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(viewState).includes(key)
          )
            ? viewState
            : DEFAULT_INITIAL_VIEW_STATE
        }
        controller={true}
        layers={layers}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

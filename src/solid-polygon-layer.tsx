import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import { GeoArrowSolidPolygonLayer } from "@geoarrow/deck.gl-layers";
import { useParquetWasm } from "./parquet";
import { useAccessorState, useTableBufferState } from "./accessor";

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
  let [dataRaw] = useModelState<DataView>("table");
  let [filled] = useModelState("filled");
  let [extruded] = useModelState("extruded");
  let [wireframe] = useModelState("wireframe");
  let [elevationScale] = useModelState("elevation_scale");
  let [getElevationRaw] = useModelState("get_elevation");
  let [getFillColorRaw] = useModelState("get_fill_color");
  let [getLineColorRaw] = useModelState("get_line_color");

  const [dataTable] = useTableBufferState(wasmReady, dataRaw);
  const [getElevation] = useAccessorState(wasmReady, getElevationRaw);
  const [getFillColor] = useAccessorState(wasmReady, getFillColorRaw);
  const [getLineColor] = useAccessorState(wasmReady, getLineColorRaw);

  const layers = [];
  if (dataTable) {
    // @ts-ignore
    const layer = new GeoArrowSolidPolygonLayer({
      id: "geoarrow-polygons",
      data: dataTable,
      ...(filled && { filled }),
      ...(extruded && { extruded }),
      ...(wireframe && { wireframe }),
      ...(elevationScale && { elevationScale }),
      ...(getElevation && { getElevation }),
      ...(getFillColor && { getFillColor }),
      ...(getLineColor && { getLineColor }),
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
        // ContextProvider={MapContext.Provider}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

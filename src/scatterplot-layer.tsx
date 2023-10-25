import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import { GeoArrowScatterplotLayer } from "@geoarrow/deck.gl-layers";
import { useParquetWasm } from "./parquet";
import { useAccessorState, useTableBufferState } from "./accessor";
import { getTooltip } from "./tooltip";

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
  let [radiusUnits] = useModelState("radius_units");
  let [radiusScale] = useModelState("radius_scale");
  let [radiusMinPixels] = useModelState("radius_min_pixels");
  let [radiusMaxPixels] = useModelState("radius_max_pixels");
  let [lineWidthUnits] = useModelState("line_width_units");
  let [lineWidthScale] = useModelState("line_width_scale");
  let [lineWidthMinPixels] = useModelState("line_width_min_pixels");
  let [lineWidthMaxPixels] = useModelState("line_width_max_pixels");
  let [stroked] = useModelState("stroked");
  let [filled] = useModelState("filled");
  let [billboard] = useModelState("billboard");
  let [antialiasing] = useModelState("antialiasing");
  let [getRadiusRaw] = useModelState("get_radius");
  let [getFillColorRaw] = useModelState("get_fill_color");
  let [getLineColorRaw] = useModelState("get_line_color");
  let [getLineWidthRaw] = useModelState("get_line_width");

  const [dataTable] = useTableBufferState(wasmReady, dataRaw);
  const [getRadius] = useAccessorState(wasmReady, getRadiusRaw);
  const [getFillColor] = useAccessorState(wasmReady, getFillColorRaw);
  const [getLineColor] = useAccessorState(wasmReady, getLineColorRaw);
  const [getLineWidth] = useAccessorState(wasmReady, getLineWidthRaw);

  const layers = [];
  if (dataTable) {
    // @ts-ignore
    const layer = new GeoArrowScatterplotLayer({
      // todo: use model.model_id?
      id: "geoarrow-points",
      data: dataTable,
      ...(radiusUnits && { radiusUnits }),
      ...(radiusScale && { radiusScale }),
      ...(radiusMinPixels && { radiusMinPixels }),
      ...(radiusMaxPixels && { radiusMaxPixels }),
      ...(lineWidthUnits && { lineWidthUnits }),
      ...(lineWidthScale && { lineWidthScale }),
      ...(lineWidthMinPixels && { lineWidthMinPixels }),
      ...(lineWidthMaxPixels && { lineWidthMaxPixels }),
      ...(stroked && { stroked }),
      ...(filled && { filled }),
      ...(billboard && { billboard }),
      ...(antialiasing && { antialiasing }),
      ...(getRadius && { getRadius }),
      ...(getFillColor && { getFillColor }),
      ...(getLineColor && { getLineColor }),
      ...(getLineWidth && { getLineWidth }),
      pickable: true,
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
        getTooltip={getTooltip}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

import * as React from "react";
import { useState, useEffect } from "react";
import { createRender, useModel, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import * as arrow from "apache-arrow";
import { GeoArrowScatterplotLayer } from "@geoarrow/deck.gl-layers";
import initParquetWasm, { readParquet } from "parquet-wasm/esm/arrow2";

const INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

const PARQUET_WASM_VERSION = "0.5.0-alpha.1";
const PARQUET_WASM_CDN_URL = `https://cdn.jsdelivr.net/npm/parquet-wasm@${PARQUET_WASM_VERSION}/esm/arrow2_bg.wasm`;

let WASM_READY: boolean = false;

/**
 * Parse a Parquet buffer to an Arrow JS table
 */
function parseParquet(dataView: DataView): arrow.Table {
  if (!WASM_READY) {
    throw new Error("wasm not ready");
  }

  console.time("readParquet");

  // TODO: use arrow-js-ffi for more memory-efficient wasm --> js transfer
  const arrowIPCBuffer = readParquet(new Uint8Array(dataView.buffer)).intoIPC();
  const arrowTable = arrow.tableFromIPC(arrowIPCBuffer);

  console.timeEnd("readParquet");

  return arrowTable;
}

// NOTE: this was an attempt to only parse Parquet for the initial data and
// whenever the data buffer changed. But I had issues where the wasm wasn't
// ready yet when the original data needed to be instantiated
//
// NOTE2: I worked around this by adding a useEffect in the main App().. so this
// function can probably be deleted
function useModelParquetState(
  key: string,
  ...deps
): [arrow.Table | undefined, (value: DataView) => void] {
  let model = useModel();

  console.log("WASM_READY", WASM_READY);
  let [table, setTable] = useState<arrow.Table | undefined>(
    WASM_READY ? parseParquet(model.get(key)) : undefined
  );
  console.log(deps);
  useEffect(() => {
    let parquetCallback = () => {
      console.log("inside parquetCallback");
      setTable(WASM_READY ? parseParquet(model.get(key)) : undefined);
    };
    model.on(`change:${key}`, parquetCallback);
    return () => model.off(`change:${key}`, parquetCallback);
  }, [model, key, deps]);

  console.log("useModelParquetState table", table);
  return [
    table,
    (value) => {
      model.set(key, value);
      model.save_changes();
    },
  ];
}

function App() {
  const [wasmReady, setWasmReady] = React.useState<boolean>(false);

  // Init parquet wasm
  React.useEffect(() => {
    const callback = async () => {
      await initParquetWasm(PARQUET_WASM_CDN_URL);
      setWasmReady(true);
      WASM_READY = true;
    };

    callback();
  }, []);

  let [dataView] = useModelState<DataView>("table_buffer");

  const [dataTable, setDataTable] = useState<arrow.Table | null>(null);

  // Only parse the table's parquet buffer when the buffer itself or wasmReady
  // has changed
  useEffect(() => {
    const callback = () => {
      if (wasmReady && dataView && dataView.byteLength > 0) {
        const arrowTable = parseParquet(dataView);
        setDataTable(arrowTable);
      }
    };

    callback();
  }, [wasmReady, dataView]);

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
  let [getRadius] = useModelState("get_radius");
  let [getFillColor] = useModelState("get_fill_color");
  let [getLineColor] = useModelState("get_line_color");
  let [getLineWidth] = useModelState("get_line_width");

  const layers = [];
  if (wasmReady && dataTable) {
    // @ts-ignore
    const layer = new GeoArrowScatterplotLayer({
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
      ...(getRadius && {
        getRadius:
          getRadius instanceof DataView
            ? parseParquet(getRadius).getChildAt(0)
            : getRadius,
      }),
      ...(getFillColor && {
        getFillColor:
          getFillColor instanceof DataView
            ? parseParquet(getFillColor).getChildAt(0)
            : getFillColor,
      }),
      ...(getLineColor && {
        getLineColor:
          getLineColor instanceof DataView
            ? parseParquet(getLineColor).getChildAt(0)
            : getLineColor,
      }),
      ...(getLineWidth && {
        getLineWidth:
          getLineWidth instanceof DataView
            ? parseParquet(getLineWidth).getChildAt(0)
            : getLineWidth,
      }),
    });
    layers.push(layer);
  }

  return (
    <div style={{ height: 500 }}>
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
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

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

function parseParquet(dataView: DataView): arrow.Table {
  if (!WASM_READY) {
    throw new Error("wasm not ready");
  }

  console.time("readParquet");

  // TODO: use FFI for wasm --> js transfer
  const arrowIPCBuffer = readParquet(new Uint8Array(dataView.buffer)).intoIPC();
  const arrowTable = arrow.tableFromIPC(arrowIPCBuffer);

  console.timeEnd("readParquet");

  return arrowTable;
}

// NOTE: this was an attempt to only parse Parquet for the initial data and
// whenever the data buffer changed. But I had issues where the wasm wasn't
// ready yet when the original data needed to be instantiated
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

  // TODO: useModelParquetState seems like a preferable solution because it will
  // only re-parse the parquet buffer when the data has changed, but it needs to
  // be run _after_ the wasm has been asynchronously instantiated... and I ran
  // into issues with it being run before the wasm had loaded
  // let [mainTable] = useModelParquetState("parquet_table_buffer", wasmReady);

  let [dataView] = useModelState<DataView>("table_buffer");
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
  if (wasmReady && dataView && dataView.byteLength > 0) {
    // TODO: it would be nice to re-parse this only when the data has changed,
    // and not when any other attribute has changed!
    const arrowTable = parseParquet(dataView);
    // TODO: allow other names
    const geometryColumnIndex = arrowTable.schema.fields.findIndex(
      (field) => field.name == "geometry"
    );

    const geometryField = arrowTable.schema.fields[geometryColumnIndex];
    const geoarrowTypeName = geometryField.metadata.get("ARROW:extension:name");
    switch (geoarrowTypeName) {
      case "geoarrow.point":
        {
          const layer = new GeoArrowScatterplotLayer({
            id: "geoarrow-points",
            data: arrowTable,
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
          });
          layers.push(layer);
        }
        break;

      default:
        console.warn(`no layer supported for ${geoarrowTypeName}`);
        break;
    }
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

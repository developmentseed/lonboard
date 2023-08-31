import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL, { GeoJsonLayer, ArcLayer, ScatterplotLayer } from "deck.gl";
import parquet from "parquet-wasm/esm2/arrow2.js";
import * as arrow from "@apache-arrow/es2015-esm";

console.log(parquet);

// source: Natural Earth http://www.naturalearthdata.com/ via geojson.xyz
const AIR_PORTS =
  "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_10m_airports.geojson";

const INITIAL_VIEW_STATE = {
  latitude: 51.47,
  longitude: 0.45,
  zoom: 4,
  bearing: 0,
  pitch: 30,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";
const NAV_CONTROL_STYLE = {
  position: "absolute",
  top: 10,
  left: 10,
};

function parseParquet(wasm, dataView) {
  const parquetBytes = new Uint8Array(dataView.buffer);
  const decodedArrowBytes = wasm.readParquet(parquetBytes);
  console.log(decodedArrowBytes);
  const arrowTable = arrow.tableFromIPC(decodedArrowBytes);
  return arrowTable;
}

function App() {
  let [dataView, setDataView] = useModelState("buffer");
  let [wasm, updateWasm] = React.useState();
  React.useEffect(() => {
    const initializeWasm = async () => {
      const parquetWasm = await parquet(
        "https://unpkg.com/parquet-wasm@0.4.0/esm2/arrow2_bg.wasm"
      );
      updateWasm(parquetWasm);
    };
    initializeWasm();
  }, []);

  console.log("dataView");
  console.log(dataView);
  // console.log(ScatterplotLayer);

  const onClick = (info) => {
    if (info.object) {
      // eslint-disable-next-line
      alert(
        `${info.object.properties.name} (${info.object.properties.abbrev})`
      );
    }
  };

  const layers = [
    new GeoJsonLayer({
      id: "airports",
      data: AIR_PORTS,
      // Styles
      filled: true,
      pointRadiusMinPixels: 2,
      pointRadiusScale: 2000,
      getPointRadius: (f) => 11 - f.properties.scalerank,
      getFillColor: [200, 0, 80, 180],
      // Interactive props
      pickable: true,
      autoHighlight: true,
      onClick,
    }),
    new ArcLayer({
      id: "arcs",
      data: AIR_PORTS,
      dataTransform: (d) =>
        d.features.filter((f) => f.properties.scalerank < 4),
      // Styles
      getSourcePosition: (f) => [-0.4531566, 51.4709959], // London
      getTargetPosition: (f) => f.geometry.coordinates,
      getSourceColor: [0, 128, 200],
      getTargetColor: [200, 0, 80],
      getWidth: 1,
    }),
  ];
  if (wasm && dataView) {
    globalThis.dataView = dataView;
    globalThis.wasm = wasm;
    console.log('hi');
    console.log(wasm);
    const arrowTable = parseParquet(wasm, dataView);
    const geometryColumn = arrowTable.getChild("geometry");
    const flatCoordinateArray = geometryColumn.getChildAt(0).data[0].values;
    const data = {
      length: arrowTable.numRows,
      // Pregenerated attributes
      attributes: {
        // Flat coordinates array; this is a view onto the Arrow Table's memory and can be copied directly to the GPU
        // Refer to https://deck.gl/docs/developer-guide/performance#supply-binary-blobs-to-the-data-prop
        getPosition: { value: flatCoordinateArray, size: 2 },
      },
    };
    const layer = new ScatterplotLayer({
      // This is an Observable hack - changing the id will force the layer to refresh when the cell reevaluates
      id: `geojson-${Date.now()}`,
      data,
      getFillColor: [255, 0, 0],
      getPointRadius: 10,
      pointRadiusMinPixels: 0.8,
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
        {/* <NavigationControl style={NAV_CONTROL_STYLE} /> */}
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

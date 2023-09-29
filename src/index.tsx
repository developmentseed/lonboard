import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "deck.gl/typed";
import * as arrow from "@apache-arrow/es2015-esm";
import { GeoArrowPointLayer } from "@geoarrow/deck.gl-layers";

// source: Natural Earth http://www.naturalearthdata.com/ via geojson.xyz
const AIR_PORTS =
  "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_10m_airports.geojson";

const INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";
const NAV_CONTROL_STYLE = {
  position: "absolute",
  top: 10,
  left: 10,
};

function App() {
  let [dataView, setDataView] = useModelState<DataView>("buffer");

  const layers = [];

  if (dataView.byteLength > 0) {
    const arrowTable = arrow.tableFromIPC(dataView.buffer);
    // TODO: allow other names
    const geometryColumnIndex = arrowTable.schema.fields.findIndex(
      (field) => field.name == "geometry"
    );

    const geometryField = arrowTable.schema.fields[geometryColumnIndex];
    const geoarrowTypeName = geometryField.metadata.get("ARROW:extension:name");
    switch (geoarrowTypeName) {
      case "geoarrow.point":
        {
          const layer = new GeoArrowPointLayer({
            id: "geoarrow-points",
            data: arrowTable,
            getFillColor: [0, 255, 0],
            getLineColor: [0, 0, 255],
            stroked: true,
            radiusMinPixels: 1,
            getPointRadius: 10,
            pointRadiusMinPixels: 0.8,
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
        {/* <NavigationControl style={NAV_CONTROL_STYLE} /> */}
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

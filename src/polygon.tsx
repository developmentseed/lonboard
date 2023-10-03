import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import * as arrow from "apache-arrow";
import { GeoArrowSolidPolygonLayer } from "@geoarrow/deck.gl-layers";

const INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

function App() {
  let [dataView] = useModelState<DataView>("table_buffer");
  let [filled] = useModelState("filled");
  let [extruded] = useModelState("extruded");
  let [wireframe] = useModelState("wireframe");
  let [elevationScale] = useModelState("elevation_scale");
  let [getElevation] = useModelState("get_elevation");
  let [getFillColor] = useModelState("get_fill_color");
  let [getLineColor] = useModelState("get_line_color");

  const layers = [];

  if (dataView && dataView.byteLength > 0) {
    const arrowTable = arrow.tableFromIPC(dataView.buffer);
    // TODO: allow other names
    const geometryColumnIndex = arrowTable.schema.fields.findIndex(
      (field) => field.name == "geometry"
    );

    const geometryField = arrowTable.schema.fields[geometryColumnIndex];
    const geoarrowTypeName = geometryField.metadata.get("ARROW:extension:name");
    switch (geoarrowTypeName) {
      case "geoarrow.polygon":
        {
          const layer = new GeoArrowSolidPolygonLayer({
            id: "geoarrow-polygons",
            data: arrowTable,
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

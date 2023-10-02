import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "deck.gl/typed";
import * as arrow from "@apache-arrow/es2015-esm";
import { GeoArrowScatterplotLayer } from "@geoarrow/deck.gl-layers";

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

  if (dataView && dataView.byteLength > 0) {
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

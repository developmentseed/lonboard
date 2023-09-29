import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "deck.gl/typed";
import * as arrow from "@apache-arrow/es2015-esm";
import { GeoArrowLineStringLayer } from "@geoarrow/deck.gl-layers";

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
  let [widthUnits] = useModelState("width_units");
  let [widthScale] = useModelState("width_scale");
  let [widthMinPixels] = useModelState("width_min_pixels");
  let [widthMaxPixels] = useModelState("width_max_pixels");
  let [jointRounded] = useModelState("joint_rounded");
  let [capRounded] = useModelState("cap_rounded");
  let [miterLimit] = useModelState("miter_limit");
  let [billboard] = useModelState("billboard");
  let [getColor] = useModelState("get_color");
  let [getWidth] = useModelState("get_width");

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
      case "geoarrow.linestring":
        {
          const layer = new GeoArrowLineStringLayer({
            id: "geoarrow-linestring",
            data: arrowTable,

            ...(widthUnits && {widthUnits}),
            ...(widthScale && {widthScale}),
            ...(widthMinPixels && {widthMinPixels}),
            ...(widthMaxPixels && {widthMaxPixels}),
            ...(jointRounded && {jointRounded}),
            ...(capRounded && {capRounded}),
            ...(miterLimit && {miterLimit}),
            ...(billboard && {billboard}),
            ...(getColor && {getColor}),
            ...(getWidth && {getWidth}),
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

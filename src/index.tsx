import * as React from "react";
import { createRender, useModelState } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL, {
  GeoJsonLayer,
  ArcLayer,
  ScatterplotLayer,
} from "deck.gl/typed";
import * as arrow from "@apache-arrow/es2015-esm";
import { GeoArrowPointLayer } from "./point";

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

  const onClick = (info) => {
    if (info.object) {
      // eslint-disable-next-line
      alert(
        `${info.object.properties.name} (${info.object.properties.abbrev})`
      );
    }
  };

  const layers = [
    // new GeoJsonLayer({
    //   id: "airports",
    //   data: AIR_PORTS,
    //   // Styles
    //   filled: true,
    //   pointRadiusMinPixels: 2,
    //   pointRadiusScale: 2000,
    //   getPointRadius: (f) => 11 - f.properties.scalerank,
    //   getFillColor: [200, 0, 80, 180],
    //   // Interactive props
    //   pickable: true,
    //   autoHighlight: true,
    //   onClick,
    // }),
    // new ArcLayer({
    //   id: "arcs",
    //   data: AIR_PORTS,
    //   dataTransform: (d) =>
    //     d.features.filter((f) => f.properties.scalerank < 4),
    //   // Styles
    //   getSourcePosition: (f) => [-0.4531566, 51.4709959], // London
    //   getTargetPosition: (f) => f.geometry.coordinates,
    //   getSourceColor: [0, 128, 200],
    //   getTargetColor: [200, 0, 80],
    //   getWidth: 1,
    // }),
  ];

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
            getFillColor: [255, 0, 0],
            radiusMinPixels: 10,
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

    // const arrowTable = arrow.tableFromIPC(dataView.buffer);
    // console.log(arrowTable);

    // for (let i = 0; i < arrowTable.batches.length; i++) {
    //   const batch = arrowTable.batches[i];
    //   const geometryColumn = batch.getChild("geometry");
    //   const flatCoordinateArray = geometryColumn.getChildAt(0).data[0].values;
    //   console.log(flatCoordinateArray);
    //   const data = {
    //     length: batch.numRows,
    //     // Pregenerated attributes
    //     attributes: {
    //       // Flat coordinates array; this is a view onto the Arrow Table's memory and can be copied directly to the GPU
    //       // Refer to https://deck.gl/docs/developer-guide/performance#supply-binary-blobs-to-the-data-prop
    //       getPosition: { value: flatCoordinateArray, size: 2 },
    //     },
    //   };
    //   const layer = new ScatterplotLayer({
    //     // This is an Observable hack - changing the id will force the layer to refresh when the cell reevaluates
    //     id: `points-${i}`,
    //     data,
    //     getFillColor: [255, 0, 0],
    //     getPointRadius: 10,
    //     pointRadiusMinPixels: 10,
    //   });
    //   layers.push(layer);
    // }
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

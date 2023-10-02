import * as React from "react";
import { useEffect, useState } from "react";
// import {} from "";
import { createRender, useModelState, useModel } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import * as arrow from "apache-arrow";
import {
  GeoArrowPathLayer,
  GeoArrowScatterplotLayer,
  GeoArrowSolidPolygonLayer,
} from "@geoarrow/deck.gl-layers";
import { Layer } from "@deck.gl/core/typed";
// import { useModel } from "./anywidget";

const INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

function createLayer() {}

async function unpack_models(model_ids: string[], manager) {
  return Promise.all(
    model_ids.map((id) => manager.get_model(id.slice("IPY_MODEL_".length)))
  );
}

// /**
//  * @template T
//  *
//  * @param {string} key
//  * @returns {[T, (value: T) => void]}
//  */
// function useLocalModelState(model, key) {
//   let [value, setValue] = React.useState(model.get(key));
//   React.useEffect(() => {
//     let callback = () => setValue(model.get(key));
//     model.on(`change:${key}`, callback);
//     return () => model.off(`change:${key}`, callback);
//   }, [model, key]);
//   return [
//     value,
//     (value) => {
//       model.set(key, value);
//       model.save_changes();
//     },
//   ];
// }

async function _getChildLayers(model): any[] {
  const modelLayerIds = model.get("layers");
  const models = await unpack_models(modelLayerIds, model.widget_manager);
}

async function _createLayers(model): Promise<Layer[]> {
  const modelLayerIds = model.get("layers");
  const models = await unpack_models(modelLayerIds, model.widget_manager);
  const layers = [];
  for (const model of models) {
    const layerType = model.get("_layer_type");
    switch (layerType) {
      case "scatterplot":
        layers.push(createScatterplotLayer(model));
        break;
      case "path":
        layers.push(createPathLayer(model));
        break;
      case "solid-polygon":
        layers.push(createSolidPolygonLayer(model));
        break;
      default:
        console.warn(`no layer supported for ${layerType}`);
        break;
    }
  }

  return layers;
}

function createScatterplotLayer(model): GeoArrowScatterplotLayer {
  let [dataView] = useLocalModelState(model, "table_buffer");
  let [radiusUnits] = useLocalModelState(model, "radius_units");
  let [radiusScale] = useLocalModelState(model, "radius_scale");
  let [radiusMinPixels] = useLocalModelState(model, "radius_min_pixels");
  let [radiusMaxPixels] = useLocalModelState(model, "radius_max_pixels");
  let [lineWidthUnits] = useLocalModelState(model, "line_width_units");
  let [lineWidthScale] = useLocalModelState(model, "line_width_scale");
  let [lineWidthMinPixels] = useLocalModelState(model, "line_width_min_pixels");
  let [lineWidthMaxPixels] = useLocalModelState(model, "line_width_max_pixels");
  let [stroked] = useLocalModelState(model, "stroked");
  let [filled] = useLocalModelState(model, "filled");
  let [billboard] = useLocalModelState(model, "billboard");
  let [antialiasing] = useLocalModelState(model, "antialiasing");
  let [getRadius] = useLocalModelState(model, "get_radius");
  let [getFillColor] = useLocalModelState(model, "get_fill_color");
  let [getLineColor] = useLocalModelState(model, "get_line_color");
  let [getLineWidth] = useLocalModelState(model, "get_line_width");

  const arrowTable = arrow.tableFromIPC(dataView.buffer);
  return new GeoArrowScatterplotLayer({
    id: model.model_id,
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
}

function createPathLayer(model): GeoArrowPathLayer {
  let [dataView] = useLocalModelState(model, "table_buffer");
  let [widthUnits] = useLocalModelState(model, "width_units");
  let [widthScale] = useLocalModelState(model, "width_scale");
  let [widthMinPixels] = useLocalModelState(model, "width_min_pixels");
  let [widthMaxPixels] = useLocalModelState(model, "width_max_pixels");
  let [jointRounded] = useLocalModelState(model, "joint_rounded");
  let [capRounded] = useLocalModelState(model, "cap_rounded");
  let [miterLimit] = useLocalModelState(model, "miter_limit");
  let [billboard] = useLocalModelState(model, "billboard");
  let [getColor] = useLocalModelState(model, "get_color");
  let [getWidth] = useLocalModelState(model, "get_width");

  const arrowTable = arrow.tableFromIPC(dataView.buffer);
  return new GeoArrowPathLayer({
    id: model.model_id,
    data: arrowTable,

    ...(widthUnits && { widthUnits }),
    ...(widthScale && { widthScale }),
    ...(widthMinPixels && { widthMinPixels }),
    ...(widthMaxPixels && { widthMaxPixels }),
    ...(jointRounded && { jointRounded }),
    ...(capRounded && { capRounded }),
    ...(miterLimit && { miterLimit }),
    ...(billboard && { billboard }),
    ...(getColor && { getColor }),
    ...(getWidth && { getWidth }),
  });
}

function createSolidPolygonLayer(model): GeoArrowSolidPolygonLayer {
  let [dataView] = useLocalModelState(model, "table_buffer");
  let [filled] = useLocalModelState(model, "filled");
  let [extruded] = useLocalModelState(model, "extruded");
  let [wireframe] = useLocalModelState(model, "wireframe");
  let [elevationScale] = useLocalModelState(model, "elevation_scale");
  let [getElevation] = useLocalModelState(model, "get_elevation");
  let [getFillColor] = useLocalModelState(model, "get_fill_color");
  let [getLineColor] = useLocalModelState(model, "get_line_color");

  const arrowTable = arrow.tableFromIPC(dataView.buffer);
  return new GeoArrowSolidPolygonLayer({
    id: model.model_id,
    data: arrowTable,
    ...(filled && { filled }),
    ...(extruded && { extruded }),
    ...(wireframe && { wireframe }),
    ...(elevationScale && { elevationScale }),
    ...(getElevation && { getElevation }),
    ...(getFillColor && { getFillColor }),
    ...(getLineColor && { getLineColor }),
  });
}
/**
 * @template T
 *
 * @param {string} key
 * @returns {[T, (value: T) => void]}
 */
function useLocalModelState(model, key: string) {
	let [value, setValue] = React.useState(model.get(key));
	React.useEffect(() => {
		let callback = () => setValue(model.get(key));
		model.on(`change:${key}`, callback);
		return () => model.off(`change:${key}`, callback);
	}, [model, key]);
	return [
		value,
		(value) => {
			model.set(key, value);
			model.save_changes();
		},
	];
}
function App() {
  let model = useModel();
  console.log("top level model");
  console.log(model);

  // let childLayerIds = model.get("layers");
  let [childLayerIds] = useModelState<string[]>("layers");
  console.log("childLayerIds", childLayerIds);

  const layers = [];
  for (const childLayerId of childLayerIds) {
    console.log(childLayerId);
    // model_ids.map((id) => manager.get_model());
    const childLayerModel = model.widget_manager._modelsSync.get(
      childLayerId.slice("IPY_MODEL_".length)
    );

    // const [getFillColor] = useLocalModelState(childLayerModel, "get_fill_color");
    // console.log("getFillColor", getFillColor);

    // const key = "get_fill_color";
    // let [value, setValue] = React.useState(childLayerModel.get(key));
    // React.useEffect(() => {
    //   let callback = () => setValue(model.get(key));
    //   model.on(`change:${key}`, callback);
    //   return () => model.off(`change:${key}`, callback);
    // }, [model, key]);
    // console.log("value", value);

    console.log(childLayerModel);

    const layerType = childLayerModel.get("_layer_type");
    switch (layerType) {
      case "scatterplot":
        layers.push(createScatterplotLayer(childLayerModel));
        break;
      case "path":
        layers.push(createPathLayer(childLayerModel));
        break;
      case "solid-polygon":
        layers.push(createSolidPolygonLayer(childLayerModel));
        break;
      default:
        console.warn(`no layer supported for ${layerType}`);
        break;
    }
  }

  console.log(layers);

  // console.log(model);

  // const [layerModels, layerModelsSet] = useState<any[]>([]);

  // useEffect(() => {
  //   async function setLayerModels() {
  //     const layers = await _createLayers(model);
  //     layersSet(layers);
  //   }

  //   setLayers();
  // }, [...childLayerIds]);

  // const manager = model.widget_manager;
  // console.log(layers);
  // const layers = [];

  // if (dataView && dataView.byteLength > 0) {
  //   const arrowTable = arrow.tableFromIPC(dataView.buffer);
  //   // TODO: allow other names
  //   const geometryColumnIndex = arrowTable.schema.fields.findIndex(
  //     (field) => field.name == "geometry"
  //   );

  //   const geometryField = arrowTable.schema.fields[geometryColumnIndex];
  //   const geoarrowTypeName = geometryField.metadata.get("ARROW:extension:name");
  //   switch (geoarrowTypeName) {
  //     case "geoarrow.point":
  //       {
  //         const layer = new GeoArrowScatterplotLayer({
  //           id: "geoarrow-points",
  //           data: arrowTable,
  //           ...(radiusUnits && { radiusUnits }),
  //           ...(radiusScale && { radiusScale }),
  //           ...(radiusMinPixels && { radiusMinPixels }),
  //           ...(radiusMaxPixels && { radiusMaxPixels }),
  //           ...(lineWidthUnits && { lineWidthUnits }),
  //           ...(lineWidthScale && { lineWidthScale }),
  //           ...(lineWidthMinPixels && { lineWidthMinPixels }),
  //           ...(lineWidthMaxPixels && { lineWidthMaxPixels }),
  //           ...(stroked && { stroked }),
  //           ...(filled && { filled }),
  //           ...(billboard && { billboard }),
  //           ...(antialiasing && { antialiasing }),
  //           ...(getRadius && { getRadius }),
  //           ...(getFillColor && { getFillColor }),
  //           ...(getLineColor && { getLineColor }),
  //           ...(getLineWidth && { getLineWidth }),
  //         });
  //         layers.push(layer);
  //       }
  //       break;

  //     default:
  //       console.warn(`no layer supported for ${geoarrowTypeName}`);
  //       break;
  //   }
  // }

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

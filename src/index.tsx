import * as React from "react";
import { useState, useEffect } from "react";
import { createRender, useModelState, useModel } from "@anywidget/react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react/typed";
import * as arrow from "apache-arrow";
import {
  GeoArrowPathLayer,
  GeoArrowScatterplotLayer,
  GeoArrowSolidPolygonLayer,
} from "@geoarrow/deck.gl-layers";
import type { Layer } from "@deck.gl/core/typed";

const INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

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

// Ref https://github.com/manzt/anywidget/pull/194
async function unpack_models(model_ids, manager) {
  console.log("unpack");
  return Promise.all(
    model_ids.map((id) => manager.get_model(id.slice("IPY_MODEL_".length)))
  );
}

function App() {
  let model = useModel();
  let [childLayerIds] = useModelState<string[]>("layers");
  let [childModels, childModelsSet] = React.useState<any[]>([]);

  React.useEffect(() => {
    async function accessChildModels() {
      let children_models = await unpack_models(
        childLayerIds,
        model.widget_manager
      );

      console.log("child_models", children_models);
      childModelsSet(children_models);
    }

    accessChildModels();
  }, [childLayerIds]);

  let [childModels, setChildModels] = useState<any[]>([]);

  useEffect(() => {
    const callback = async () => {
      const promises: Promise<any>[] = [];
      for (const childLayerId of childLayerIds) {
        promises.push(
          model.widget_manager.get_model(
            childLayerId.slice("IPY_MODEL_".length)
          )
        );
      }
      const _childModels = await Promise.all(promises);
      setChildModels(_childModels);
      console.log("_childModels");
      console.log(_childModels);
    };
    callback().catch(console.error);
  }, [...childLayerIds]);



  window.model = model;
  console.log(model);

  const deckLayers: Layer[] = [];
  for (const childModel of childModels) {
    const layerType = childModel.get("_layer_type");
    switch (layerType) {
      case "scatterplot":
        deckLayers.push(createScatterplotLayer(childModel));
        break;
      case "path":
        deckLayers.push(createPathLayer(childModel));
        break;
      case "solid-polygon":
        deckLayers.push(createSolidPolygonLayer(childModel));
        break;
      default:
        console.warn(`no layer supported for ${layerType}`);
        break;
    }
  }

  return (
    <div style={{ height: 500 }}>
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={deckLayers}
        // ContextProvider={MapContext.Provider}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

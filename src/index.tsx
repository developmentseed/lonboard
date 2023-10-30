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
import type { WidgetModel } from "@jupyter-widgets/base";
import {
  BaseGeoArrowModel,
  PathModel,
  ScatterplotModel,
  SolidPolygonModel,
} from "./model";
import { initParquetWasm } from "./parquet";

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
  let dataRaw = model.get("table");
  let radiusUnits = model.get("radius_units");
  let radiusScale = model.get("radius_scale");
  let radiusMinPixels = model.get("radius_min_pixels");
  let radiusMaxPixels = model.get("radius_max_pixels");
  let lineWidthUnits = model.get("line_width_units");
  let lineWidthScale = model.get("line_width_scale");
  let lineWidthMinPixels = model.get("line_width_min_pixels");
  let lineWidthMaxPixels = model.get("line_width_max_pixels");
  let stroked = model.get("stroked");
  let filled = model.get("filled");
  let billboard = model.get("billboard");
  let antialiasing = model.get("antialiasing");
  let getRadius = model.get("get_radius");
  let getFillColor = model.get("get_fill_color");
  let getLineColor = model.get("get_line_color");
  let getLineWidth = model.get("get_line_width");

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
  console.log("App");
  let [subModelState, setSubModelState] = useState<
    Record<string, BaseGeoArrowModel>
  >({});
  let model = useModel();
  let [childLayerIds] = useModelState<string[]>("layers");

  // Fake state just to get react to re-render when a model callback is called
  let [stateCounter, setStateCounter] = useState<Date>(new Date());
  console.log("stateCounter", stateCounter);

  // let [childModels, setChildModels] = useState<WidgetModel[]>([]);

  // TODO: delete state from subModelState when layer has been deleted (i.e.
  // when layerId is now gone.)

  console.log("childLayerIds", childLayerIds);
  useEffect(() => {
    const callback = async () => {
      // TODO: don't block on this until parsing?
      await initParquetWasm();
      console.log("subModelState1", subModelState);

      const promises: Promise<WidgetModel>[] = [];
      for (const childLayerId of childLayerIds) {
        promises.push(
          model.widget_manager.get_model(
            childLayerId.slice("IPY_MODEL_".length)
          )
        );
      }
      const childModels = await Promise.all(promises);

      const newSubModelState: Record<string, BaseGeoArrowModel> = {
        ...subModelState,
      };
      for (let i = 0; i < childLayerIds.length; i++) {
        const childLayerId = childLayerIds[i];
        const childModel = childModels[i];

        const layerType = childModel.get("_layer_type");
        switch (layerType) {
          case "scatterplot":
            if (!newSubModelState[childLayerId]) {
              newSubModelState[childLayerId] = new ScatterplotModel(
                childModel,
                () => setStateCounter(new Date())
              );
            }
            break;
          case "path":
            if (!newSubModelState[childLayerId]) {
              newSubModelState[childLayerId] = new PathModel(childModel, () =>
                setStateCounter(new Date())
              );
            }
            break;
          case "solid-polygon":
            if (!newSubModelState[childLayerId]) {
              newSubModelState[childLayerId] = new SolidPolygonModel(
                childModel,
                () => setStateCounter(new Date())
              );
            }
            break;
          default:
            console.warn(`no layer supported for ${layerType}`);
            break;
        }
      }
      setSubModelState(newSubModelState);
    };
    callback().catch(console.error);
  }, [childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  return (
    <div style={{ height: 500 }}>
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}

export let render = createRender(App);

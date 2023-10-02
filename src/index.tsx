import * as React from "react";
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

function App() {
  let model = useModel();
  let [childLayerIds] = useModelState<string[]>("layers");

  const deckLayers: Layer[] = [];
  for (const childLayerId of childLayerIds) {
    // NOTE: The public way to access these models is via
    // `model.widget_manager.get_model()` but that's async, so I'm hacking and
    // using `_modelsSync` for now. Should probably use the public function in
    // the future?

    const childLayerModel = model.widget_manager._modelsSync.get(
      childLayerId.slice("IPY_MODEL_".length)
    );

    const layerType = childLayerModel.get("_layer_type");
    switch (layerType) {
      case "scatterplot":
        deckLayers.push(createScatterplotLayer(childLayerModel));
        break;
      case "path":
        deckLayers.push(createPathLayer(childLayerModel));
        break;
      case "solid-polygon":
        deckLayers.push(createSolidPolygonLayer(childLayerModel));
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

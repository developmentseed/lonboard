import * as React from "react";
import Map from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { isDefined } from "../util.js";
import { getTooltip } from "../tooltip/index.js";
import { MachineContext } from "../xstate";
import * as selectors from "../xstate/selectors";
import { useMapLogic } from "../hooks/useMapLogic.js";
import type { RendererProps } from "../types/rendererProps.js";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

export function MaplibreRenderer(props: RendererProps) {
  const { mapStyle, showTooltip, pickingRadius, useDevicePixels, parameters, customAttribution } = props;

  const bboxSelectPolygonLayer = MachineContext.useSelector(
    selectors.getBboxSelectPolygonLayer,
  );

  const {
    layers,
    initialViewState,
    onMapClickHandler,
    onMapHoverHandler,
    onViewStateChange,
    isDrawingBBoxSelection,
  } = useMapLogic();

  return (
    <DeckGL
      style={{ width: "100%", height: "100%" }}
      initialViewState={
        ["longitude", "latitude", "zoom"].every((key) =>
          Object.keys(initialViewState).includes(key),
        )
          ? initialViewState
          : DEFAULT_INITIAL_VIEW_STATE
      }
      controller={true}
      layers={
        bboxSelectPolygonLayer
          ? layers.concat(bboxSelectPolygonLayer)
          : layers
      }
      getTooltip={(showTooltip && getTooltip) || undefined}
      getCursor={() => (isDrawingBBoxSelection ? "crosshair" : "grab")}
      pickingRadius={pickingRadius}
      onClick={onMapClickHandler}
      onHover={onMapHoverHandler}
      useDevicePixels={isDefined(useDevicePixels) ? useDevicePixels : true}
      _typedArrayManagerProps={{
        overAlloc: 1,
        poolSize: 0,
      }}
      onViewStateChange={onViewStateChange}
      parameters={parameters}
    >
      <Map
        mapStyle={mapStyle}
        attributionControl={{
          customAttribution: customAttribution || undefined
        }}
      />
    </DeckGL>
  );
}
import DeckGL from "@deck.gl/react";
import React from "react";
import Map from "react-map-gl/maplibre";
import type { MapRendererProps } from "./types";

/**
 * DeckFirst renderer: DeckGL wraps Map component
 *
 * In this rendering mode, deck.gl is the parent component that manages
 * the canvas and view state, with the map rendered as a child component.
 * This is the traditional approach where deck.gl has full control over
 * the rendering pipeline.
 */
const DeckFirst: React.FC<MapRendererProps> = ({
  mapStyle,
  customAttribution,
  initialViewState,
  layers,
  deckRef,
  getTooltip,
  isDrawingBBoxSelection,
  pickingRadius,
  useDevicePixels,
  parameters,
  onMapClick,
  onMapHover,
  onViewStateChange,
}) => {
  return (
    <DeckGL
      ref={deckRef}
      style={{ width: "100%", height: "100%" }}
      initialViewState={initialViewState}
      controller={true}
      layers={layers}
      getTooltip={getTooltip}
      getCursor={() => (isDrawingBBoxSelection ? "crosshair" : "grab")}
      pickingRadius={pickingRadius}
      onClick={onMapClick}
      onHover={onMapHover}
      // @ts-expect-error useDevicePixels should allow number
      // https://github.com/visgl/deck.gl/pull/9826
      useDevicePixels={useDevicePixels}
      // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
      _typedArrayManagerProps={{
        overAlloc: 1,
        poolSize: 0,
      }}
      onViewStateChange={onViewStateChange}
      parameters={parameters}
    >
      <Map mapStyle={mapStyle} customAttribution={customAttribution}></Map>
    </DeckGL>
  );
};

export default DeckFirst;

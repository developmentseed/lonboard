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
const DeckFirstRenderer: React.FC<MapRendererProps> = (mapProps) => {
  // Remove maplibre-specific props before passing to DeckGL
  const { mapStyle, customAttribution, deckRef, ...deckProps } = mapProps;
  return (
    <DeckGL
      ref={deckRef}
      style={{ width: "100%", height: "100%" }}
      controller={true}
      // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
      _typedArrayManagerProps={{
        overAlloc: 1,
        poolSize: 0,
      }}
      {...deckProps}
    >
      <Map mapStyle={mapStyle} customAttribution={customAttribution}></Map>
    </DeckGL>
  );
};

export default DeckFirstRenderer;

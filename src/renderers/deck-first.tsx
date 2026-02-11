import DeckGL from "@deck.gl/react";
import type React from "react";
import MapGL from "react-map-gl/maplibre";

import type { DeckFirstRendererProps, MapRendererProps } from "./types";

/**
 * DeckFirst renderer: DeckGL wraps Map component
 *
 * In this rendering mode, deck.gl is the parent component that manages
 * the canvas and view state, with the map rendered as a child component.
 * This is the traditional approach where deck.gl has full control over
 * the rendering pipeline.
 */
const DeckFirstRenderer: React.FC<MapRendererProps & DeckFirstRendererProps> = (
  mapProps,
) => {
  // Remove maplibre-specific props before passing to DeckGL
  const {
    controls,
    mapStyle,
    customAttribution,
    deckRef,
    renderBasemap,
    ...deckProps
  } = mapProps;
  return (
    <DeckGL
      ref={deckRef}
      style={{ width: "100%", height: "100%" }}
      controller={true}
      {...deckProps}
    >
      {controls.map((control) => control.renderDeck())}
      {renderBasemap && (
        <MapGL mapStyle={mapStyle} customAttribution={customAttribution} />
      )}
    </DeckGL>
  );
};

export default DeckFirstRenderer;

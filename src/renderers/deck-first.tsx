import DeckGL from "@deck.gl/react";
import React from "react";
import MapGL from "react-map-gl/maplibre";

import { flyTo } from "../actions/fly-to";
import type { FlyToMessage } from "../types";
import type { DeckFirstRendererProps, MapRendererProps, RendererRef } from "./types";

/**
 * DeckFirst renderer: DeckGL wraps Map component
 *
 * In this rendering mode, deck.gl is the parent component that manages
 * the canvas and view state, with the map rendered as a child component.
 * This is the traditional approach where deck.gl has full control over
 * the rendering pipeline.
 */
const DeckFirstRenderer = React.forwardRef<
  RendererRef,
  MapRendererProps & DeckFirstRendererProps
>((mapProps, ref) => {
  // Remove maplibre-specific props before passing to DeckGL
  const {
    controls,
    mapStyle,
    customAttribution,
    deckRef,
    renderBasemap,
    setViewState,
    ...deckProps
  } = mapProps;

  React.useImperativeHandle(ref, () => ({
    flyTo(msg: FlyToMessage) {
      flyTo(msg, setViewState);
    },
  }));

  return (
    <DeckGL
      ref={deckRef}
      style={{ width: "100%", height: "100%" }}
      controller={true}
      {...deckProps}
    >
      {controls.map((control) => control.renderDeck())}
      {renderBasemap && (
        <MapGL
          mapStyle={mapStyle}
          attributionControl={{ customAttribution }}
        />
      )}
    </DeckGL>
  );
});

export default DeckFirstRenderer;

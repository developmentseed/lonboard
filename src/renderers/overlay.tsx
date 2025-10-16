import { _GlobeView as GlobeView } from "@deck.gl/core";
import { MapboxOverlay, MapboxOverlayProps } from "@deck.gl/mapbox";
import React from "react";
import Map, { useControl } from "react-map-gl/maplibre";

import type { MapRendererProps, OverlayRendererProps } from "./types";

/**
 * DeckGLOverlay component that integrates deck.gl with react-map-gl
 *
 * Uses the useControl hook to create a MapboxOverlay instance that
 * renders deck.gl layers on top of the base map.
 */
function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

/**
 * Overlay renderer: Map wraps DeckGLOverlay component
 *
 * In this rendering mode, the map is the parent component that controls
 * the view state, with deck.gl layers rendered as an overlay using the
 * MapboxOverlay. This approach gives the base map more control and can
 * enable features like interleaved rendering between map and deck layers.
 */
const OverlayRenderer: React.FC<MapRendererProps & OverlayRendererProps> = (
  mapProps,
) => {
  // Remove maplibre-specific props before passing to DeckGL
  const { mapStyle, customAttribution, initialViewState, views, ...deckProps } =
    mapProps;
  const firstView = Array.isArray(views) ? views[0] : views;
  const isGlobeView = firstView instanceof GlobeView;
  return (
    <Map
      reuseMaps
      initialViewState={initialViewState}
      mapStyle={mapStyle}
      attributionControl={{ customAttribution }}
      style={{ width: "100%", height: "100%" }}
      {...(isGlobeView && { projection: "globe" })}
    >
      <DeckGLOverlay
        // https://deck.gl/docs/api-reference/core/deck#_typedarraymanagerprops
        _typedArrayManagerProps={{
          overAlloc: 1,
          poolSize: 0,
        }}
        {...deckProps}
      />
    </Map>
  );
};

export default OverlayRenderer;

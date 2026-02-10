import type { MapboxOverlayProps } from "@deck.gl/mapbox";
import { MapboxOverlay } from "@deck.gl/mapbox";
import type React from "react";
import type { ViewStateChangeEvent } from "react-map-gl/maplibre";
import MapGL, { useControl } from "react-map-gl/maplibre";
import { isGlobeView } from "../util";
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
  const {
    controls,
    mapStyle,
    customAttribution,
    initialViewState,
    views,
    onViewStateChange,
    ...deckProps
  } = mapProps;
  const onMoveEnd = onViewStateChange
    ? (evt: ViewStateChangeEvent) => {
        const viewState = {
          longitude: evt.viewState.longitude,
          latitude: evt.viewState.latitude,
          zoom: evt.viewState.zoom,
          pitch: evt.viewState.pitch,
          bearing: evt.viewState.bearing,
        };
        onViewStateChange({ viewId: "mapLibreId", viewState });
      }
    : undefined;
  return (
    <MapGL
      reuseMaps
      initialViewState={initialViewState}
      mapStyle={mapStyle}
      attributionControl={{ customAttribution }}
      style={{ width: "100%", height: "100%" }}
      onMoveEnd={onMoveEnd}
      {...(isGlobeView(views) && { projection: "globe" })}
    >
      {controls.map((control) => control.renderMaplibre())}
      <DeckGLOverlay {...deckProps} />
    </MapGL>
  );
};

export default OverlayRenderer;

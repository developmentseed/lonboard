import React from "react";
import Map, { useControl } from "react-map-gl/maplibre";
import { MapboxOverlay, MapboxOverlayProps } from "@deck.gl/mapbox";
import type { MapRendererProps } from "./types";

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
const Overlay: React.FC<MapRendererProps> = ({
  mapStyle,
  customAttribution,
  initialViewState,
  layers,
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
    <Map
      reuseMaps
      initialViewState={initialViewState}
      mapStyle={mapStyle}
      attributionControl={{ customAttribution }}
      style={{ width: "100%", height: "100%" }}
    >
      <DeckGLOverlay
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
      />
    </Map>
  );
};

export default Overlay;

import type { MapLibreOverlayProps } from "@deck.gl/maplibre";
import { MapLibreOverlay } from "@deck.gl/maplibre";
import React from "react";
import type { MapRef, ViewStateChangeEvent } from "react-map-gl/maplibre";
import MapGL, { useControl, useMap } from "react-map-gl/maplibre";
import type { FlyToMessage } from "../types";
import { getRepeat, isGlobeView, omitUndefined } from "../util";
import type {
  MapRendererProps,
  OverlayRendererProps,
  RendererRef,
} from "./types";

/**
 * DeckGLOverlay component that integrates deck.gl with react-map-gl
 *
 * Uses the useControl hook to create a MapLibreOverlay instance that
 * renders deck.gl layers on top of the base map.
 */
function DeckGLOverlay(props: MapLibreOverlayProps) {
  const overlay = useControl(() => new MapLibreOverlay(props));
  overlay.setProps(props);

  // Workaround for https://github.com/visgl/deck.gl/issues/10733
  //
  // In interleaved mode the overlay adds its layers to the map's style when
  // the props change, but only if the basemap has finished loading. On first
  // load it hasn't, so the layers are drawn over the labels and under the
  // water. Pass the props again whenever the map has finished loading.
  const { current: map } = useMap();
  const propsRef = React.useRef(props);
  propsRef.current = props;
  React.useEffect(() => {
    if (!map) return;
    const onIdle = () => overlay.setProps(propsRef.current);
    map.on("idle", onIdle);
    return () => {
      map.off("idle", onIdle);
    };
  }, [map, overlay]);

  return null;
}

/**
 * Overlay renderer: Map wraps DeckGLOverlay component
 *
 * In this rendering mode, the map is the parent component that controls
 * the view state, with deck.gl layers rendered as an overlay using the
 * MapLibreOverlay. This approach gives the base map more control and can
 * enable features like interleaved rendering between map and deck layers.
 */
const OverlayRenderer = React.forwardRef<
  RendererRef,
  MapRendererProps & OverlayRendererProps
>((mapProps, ref) => {
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

  const mapRef = React.useRef<MapRef>(null);

  React.useImperativeHandle(ref, () => ({
    flyTo(msg: FlyToMessage) {
      const map = mapRef.current?.getMap();
      if (!map) return;
      map.flyTo({
        center: [msg.longitude, msg.latitude],
        zoom: msg.zoom,
        duration:
          msg.transitionDuration === "auto"
            ? undefined
            : msg.transitionDuration,
        ...omitUndefined({
          pitch: msg.pitch,
          bearing: msg.bearing,
          curve: msg.curve,
          speed: msg.speed,
          screenSpeed: msg.screenSpeed,
        }),
      });
    },
  }));

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
      ref={mapRef}
      reuseMaps
      initialViewState={initialViewState}
      mapStyle={mapStyle}
      attributionControl={{ customAttribution }}
      style={{ width: "100%", height: "100%" }}
      onMoveEnd={onMoveEnd}
      {...(isGlobeView(views) && { projection: "globe" })}
      // MapLibre repeats the world by default, so only pass `repeat` when set
      {...omitUndefined({ renderWorldCopies: getRepeat(views) })}
    >
      {controls.map((control) => control.renderMaplibre())}
      <DeckGLOverlay {...deckProps} />
    </MapGL>
  );
});

export default OverlayRenderer;

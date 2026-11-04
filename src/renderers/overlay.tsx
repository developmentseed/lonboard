import type { MapLibreOverlayProps } from "@deck.gl/maplibre";
import { MapLibreOverlay } from "@deck.gl/maplibre";
import type { Map as MaplibreMap } from "maplibre-gl";
import React from "react";
import type { MapRef, ViewStateChangeEvent } from "react-map-gl/maplibre";
import MapGL, { useControl, useMap } from "react-map-gl/maplibre";
import type { FlyToMessage } from "../types";
import type { Camera } from "../util";
import { getRepeat, isGlobeView, omitUndefined } from "../util";
import type {
  MapRendererProps,
  OverlayRendererProps,
  RendererRef,
} from "./types";

/**
 * Whether the map's camera is already at `viewState`.
 *
 * Keys that `viewState` doesn't define are not compared, because not every
 * view state has all of them. E.g. a globe view state has no pitch or bearing.
 */
function isAtViewState(map: MaplibreMap, viewState: Camera): boolean {
  const { lng, lat } = map.getCenter();
  const camera: Required<Camera> = {
    longitude: lng,
    latitude: lat,
    zoom: map.getZoom(),
    pitch: map.getPitch(),
    bearing: map.getBearing(),
  };
  return (Object.keys(camera) as (keyof Camera)[]).every(
    (key) => viewState[key] == null || viewState[key] === camera[key],
  );
}

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
    // The map reports its camera with `saveCamera` instead
    onViewStateChange: _onViewStateChange,
    saveCamera,
    ...deckProps
  } = mapProps;

  const mapRef = React.useRef<MapRef>(null);

  // True while the map moves to a view state that it was given, which must not
  // be reported back to Python.
  const isSettingViewState = React.useRef(false);

  // MapLibre only reads `initialViewState` when the map is created, so a view
  // state set later, from Python or by `jslink`, has to be applied here. The
  // map's own reports come back here too, and are skipped because the map is
  // already there.
  React.useEffect(() => {
    const map = mapRef.current?.getMap();
    const viewState = initialViewState as Camera | null | undefined;
    if (!map || !viewState) return;

    const { longitude, latitude, zoom, pitch, bearing } = viewState;
    if (longitude == null || latitude == null) return;
    if (isAtViewState(map, viewState)) return;

    isSettingViewState.current = true;
    try {
      map.jumpTo({
        center: [longitude, latitude],
        ...(zoom != null && { zoom }),
        ...(pitch != null && { pitch }),
        ...(bearing != null && { bearing }),
      });
    } finally {
      isSettingViewState.current = false;
    }
  }, [initialViewState]);

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

  const onMoveEnd = (evt: ViewStateChangeEvent) => {
    if (isSettingViewState.current) return;

    saveCamera({
      longitude: evt.viewState.longitude,
      latitude: evt.viewState.latitude,
      zoom: evt.viewState.zoom,
      pitch: evt.viewState.pitch,
      bearing: evt.viewState.bearing,
    });
  };

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

import type { MapViewState } from "@deck.gl/core";
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

/** The parts of a view state that position the MapLibre camera. */
const CAMERA_KEYS = [
  "longitude",
  "latitude",
  "zoom",
  "pitch",
  "bearing",
] as const;

type Camera = Partial<Pick<MapViewState, (typeof CAMERA_KEYS)[number]>>;

/** How many reported cameras to remember when Python doesn't send them back. */
const MAX_REPORTED_CAMERAS = 16;

/**
 * Whether `viewState` positions the camera where `reported` does.
 *
 * Keys that `viewState` doesn't define are not compared, because not every
 * view state has all of them. E.g. a globe view state has no pitch or bearing.
 */
function isSameCamera(viewState: Camera, reported: Camera): boolean {
  return CAMERA_KEYS.every(
    (key) => viewState[key] == null || viewState[key] === reported[key],
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
    onViewStateChange,
    ...deckProps
  } = mapProps;

  const mapRef = React.useRef<MapRef>(null);

  // The cameras that the map reported to Python and that Python can still send
  // back, oldest first. Python sends every reported view state back with
  // default values filled in, which must not move the map.
  //
  // Limits: reports, including the map's own one below, are recognised by
  // value. Only the last 16 are kept, so the map moves when Python sends back
  // an older one, e.g. when the kernel was busy during many pans.
  const reportedCameras = React.useRef<Camera[]>([]);
  // The camera that the map reported last, until it has come back through
  // `initialViewState`. It does so right away, before Python has seen it.
  const ownReport = React.useRef<Camera | null>(null);
  // True while the map moves to a view state set from Python, which must not
  // be reported back to Python.
  const isSettingViewState = React.useRef(false);

  // MapLibre only reads `initialViewState` when the map is created, so a view
  // state that Python sets later has to be applied to the map here.
  React.useEffect(() => {
    const map = mapRef.current?.getMap();
    const viewState = initialViewState as Camera | null | undefined;
    if (!map || !viewState) return;

    const { longitude, latitude, zoom, pitch, bearing } = viewState;
    if (longitude == null || latitude == null) return;
    if (ownReport.current && isSameCamera(viewState, ownReport.current)) {
      ownReport.current = null;
      return;
    }

    // Python sends the reported view states back in the order that it received
    // them, so nothing older than the one it sent back is still to come.
    const index = reportedCameras.current.findIndex((reported) =>
      isSameCamera(viewState, reported),
    );
    if (index >= 0) {
      reportedCameras.current = reportedCameras.current.slice(index);
      return;
    }

    reportedCameras.current = [];
    ownReport.current = null;
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

  const onMoveEnd = onViewStateChange
    ? (evt: ViewStateChangeEvent) => {
        if (isSettingViewState.current) return;

        const viewState = {
          longitude: evt.viewState.longitude,
          latitude: evt.viewState.latitude,
          zoom: evt.viewState.zoom,
          pitch: evt.viewState.pitch,
          bearing: evt.viewState.bearing,
        };
        reportedCameras.current = [...reportedCameras.current, viewState].slice(
          -MAX_REPORTED_CAMERAS,
        );
        ownReport.current = viewState;
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

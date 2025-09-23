import * as React from "react";
import { useRef, useCallback } from "react";
import Map, { MapRef } from "react-map-gl/maplibre";
import { Deck } from "@deck.gl/core";
import { isDefined } from "../util.js";
import { getTooltip } from "../tooltip/index.js";
import { MachineContext } from "../xstate";
import * as selectors from "../xstate/selectors";
import { useMapLogic } from "../hooks/useMapLogic.js";
import type { RendererProps } from "../types/rendererProps.js";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

export function DeckGLRenderer(props: RendererProps) {
  const { mapStyle, showTooltip, pickingRadius, useDevicePixels, parameters, customAttribution } = props;

  const mapRef = useRef<MapRef>(null);
  const deckRef = useRef<Deck>(null);

  const bboxSelectPolygonLayer = MachineContext.useSelector(
    selectors.getBboxSelectPolygonLayer,
  );

  const {
    layers,
    initialViewState,
    onMapClickHandler,
    onMapHoverHandler,
    onViewStateChange,
    isDrawingBBoxSelection,
  } = useMapLogic();

  const onMapLoad = useCallback(() => {
    const map = mapRef.current?.getMap();
    if (!map || !deckRef.current) return;

    deckRef.current.setProps({
      gl: map.painter.context.gl as WebGL2RenderingContext,
    });

    map.on("render", () => {
      if (deckRef.current) {
        deckRef.current.redraw();
      }
    });
  }, []);

  const onMapRender = useCallback(() => {
    if (deckRef.current) {
      deckRef.current.redraw();
    }
  }, []);

  React.useEffect(() => {
    if (!deckRef.current) {
      const deck = new Deck({
        canvas: "deck-canvas",
        width: "100%",
        height: "100%",
        initialViewState: 
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(initialViewState).includes(key),
          )
            ? initialViewState
            : DEFAULT_INITIAL_VIEW_STATE,
        controller: true,
        layers: bboxSelectPolygonLayer
          ? layers.concat(bboxSelectPolygonLayer)
          : layers,
        getTooltip: (showTooltip && getTooltip) || undefined,
        getCursor: () => (isDrawingBBoxSelection ? "crosshair" : "grab"),
        pickingRadius,
        onClick: onMapClickHandler,
        onHover: onMapHoverHandler,
        useDevicePixels: isDefined(useDevicePixels) ? useDevicePixels : true,
        _typedArrayManagerProps: {
          overAlloc: 1,
          poolSize: 0,
        },
        onViewStateChange,
        parameters: parameters || {},
      });

      deckRef.current = deck;
    } else {
      deckRef.current.setProps({
        layers: bboxSelectPolygonLayer
          ? layers.concat(bboxSelectPolygonLayer)
          : layers,
        getTooltip: (showTooltip && getTooltip) || undefined,
        getCursor: () => (isDrawingBBoxSelection ? "crosshair" : "grab"),
        pickingRadius,
        useDevicePixels: isDefined(useDevicePixels) ? useDevicePixels : true,
        parameters: parameters,
      });
    }
  }, [
    layers,
    bboxSelectPolygonLayer,
    showTooltip,
    isDrawingBBoxSelection,
    pickingRadius,
    useDevicePixels,
    parameters,
    onMapClickHandler,
    onMapHoverHandler,
    onViewStateChange,
  ]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Map
        ref={mapRef}
        mapStyle={mapStyle}
        initialViewState={
          ["longitude", "latitude", "zoom"].every((key) =>
            Object.keys(initialViewState).includes(key),
          )
            ? initialViewState
            : DEFAULT_INITIAL_VIEW_STATE
        }
        onLoad={onMapLoad}
        onRender={onMapRender}
        onMove={onViewStateChange}
        style={{ width: "100%", height: "100%" }}
        attributionControl={{
          customAttribution: customAttribution || undefined
        }}
      />
      <canvas
        id="deck-canvas"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
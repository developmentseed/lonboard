/**
 * Globe components for MapLibre globe projection with DeckGL overlay.
 * - GlobeMap: low-level MapLibre + MapboxOverlay bridge
 * - GlobeWidget: minimal widget wrapper (basemap + data layers)
 */

import * as React from "react";
import { useEffect, useState } from "react";
import Map, { useControl, type MapRef } from "react-map-gl/maplibre";
import { type Layer, type MapViewState } from "@deck.gl/core";
import {
  MapboxOverlay as DeckOverlay,
  MapboxOverlayProps,
} from "@deck.gl/mapbox";
import { useModel, useModelState } from "@anywidget/react";
import type { WidgetModel, IWidgetManager } from "@jupyter-widgets/base";
import { BaseLayerModel, initializeLayer } from "./model/index.js";
import { isDefined, loadChildModels } from "./util.js";
import { useViewStateDebounced } from "./state";

import "maplibre-gl/dist/maplibre-gl.css";

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

const DEFAULT_MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

/** Integrates DeckGL with MapLibre via MapboxOverlay. */
function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl(() => new DeckOverlay(props));
  overlay.setProps(props);
  return null;
}

interface GlobeMapProps {
  /** Initial view state for the map */
  initialViewState?: {
    latitude?: number;
    longitude?: number;
    zoom?: number;
    bearing?: number;
    pitch?: number;
  };
  /** MapLibre style URL */
  mapStyle?: string;
  /** DeckGL layers to render */
  layers?: Layer[];
  /** Custom attribution string */
  customAttribution?: string;
  /** Whether to use device pixels */
  useDevicePixels?: boolean;
  /** Picking radius in pixels */
  pickingRadius?: number;
  /** Map ID for testing purposes */
  mapId?: string;
}

/** GlobeMap: renders a MapLibre map with a DeckGL overlay. */
export function GlobeMap({
  initialViewState = DEFAULT_INITIAL_VIEW_STATE,
  mapStyle = DEFAULT_MAP_STYLE,
  layers = [],
  customAttribution,
  useDevicePixels = true,
  pickingRadius = 5,
  mapId = "globe-map",
}: GlobeMapProps) {
  const mapRef = React.useRef<MapRef | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  return (
    <div
      ref={containerRef}
      id={mapId}
      style={{ width: "100%", height: "100%" }}
    >
      <Map
        ref={mapRef}
        reuseMaps
        initialViewState={initialViewState}
        mapStyle={mapStyle}
        attributionControl={{ customAttribution }}
        projection="globe"
        onLoad={(e) => {
          // Expose underlying MapLibre instance on the globe container for tests
          const mapInstance = (e as unknown as { target?: unknown }).target;
          if (containerRef.current) {
            (containerRef.current as unknown as { _map?: unknown })._map =
              mapInstance as unknown;
          }
        }}
      >
        <DeckGLOverlay
          layers={layers}
          useDevicePixels={useDevicePixels}
          pickingRadius={pickingRadius}
          // TypedArray manager props for performance
          _typedArrayManagerProps={{
            overAlloc: 1,
            poolSize: 0,
          }}
        />
      </Map>
    </div>
  );
}

export default GlobeMap;

// Minimal widget wrapper for globe mode with only basemap + data layers
export function GlobeWidget() {
  const model = useModel();
  const [mapStyle] = useModelState<string>("basemap_style");
  const [mapHeight] = useModelState<string>("height");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [useDevicePixels] = useModelState<number | boolean>(
    "use_device_pixels",
  );
  const [customAttribution] = useModelState<string>("custom_attribution");

  const [initialViewState] = useViewStateDebounced<MapViewState>("view_state");

  const [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});
  const [childLayerIds] = useModelState<string[]>("layers");

  // Minimal child model loader (no extra features)
  async function getChildModelState(
    childModels: WidgetModel[],
    childLayerIdsLocal: string[],
    previousSubModelState: Record<string, BaseLayerModel>,
    setStateCounter: React.Dispatch<React.SetStateAction<Date>>,
  ): Promise<Record<string, BaseLayerModel>> {
    const newSubModelState: Record<string, BaseLayerModel> = {};
    const updateStateCallback = () => setStateCounter(new Date());
    for (let i = 0; i < childLayerIdsLocal.length; i++) {
      const childLayerId = childLayerIdsLocal[i];
      const childModel = childModels[i];
      if (childLayerId in previousSubModelState) {
        newSubModelState[childLayerId] = previousSubModelState[childLayerId];
        delete previousSubModelState[childLayerId];
        continue;
      }
      const childLayer = await initializeLayer(childModel, updateStateCallback);
      newSubModelState[childLayerId] = childLayer;
    }
    for (const prev of Object.values(previousSubModelState)) {
      prev.finalize();
    }
    return newSubModelState;
  }

  // Fake state to trigger re-render when model callbacks fire
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [stateCounter, setStateCounter] = useState<Date>(new Date());

  useEffect(() => {
    const loadAndUpdateLayers = async () => {
      try {
        const childModels = await loadChildModels(
          model.widget_manager as unknown as IWidgetManager,
          childLayerIds,
        );
        const newSubModelState = await getChildModelState(
          childModels,
          childLayerIds,
          subModelState,
          setStateCounter,
        );
        setSubModelState(newSubModelState);
      } catch (e) {
        console.error("Error loading child models (globe)", e);
      }
    };
    loadAndUpdateLayers();
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore react-hooks/exhaustive-deps rule configured in repo
  }, [childLayerIds]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  return (
    <div
      className="lonboard"
      style={{ minHeight: "100%", height: mapHeight }}
      data-jp-suppress-context-menu
    >
      <div className="h-full w-full relative">
        <GlobeMap
          mapStyle={mapStyle || DEFAULT_MAP_STYLE}
          customAttribution={customAttribution}
          layers={layers}
          pickingRadius={pickingRadius}
          useDevicePixels={
            isDefined(useDevicePixels) && typeof useDevicePixels === "boolean"
              ? useDevicePixels
              : true
          }
          initialViewState={
            ["longitude", "latitude", "zoom"].every((key) =>
              Object.keys(initialViewState).includes(key),
            )
              ? initialViewState
              : DEFAULT_INITIAL_VIEW_STATE
          }
          mapId="globe-map"
        />
      </div>
    </div>
  );
}

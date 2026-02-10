import { createRender, useModel, useModelState } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import type { MapViewState, PickingInfo } from "@deck.gl/core";
import type { PolygonLayerProps } from "@deck.gl/layers";
import { PolygonLayer } from "@deck.gl/layers";
import type { DeckGLRef } from "@deck.gl/react";
import type { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import type { IWidgetManager } from "@jupyter-widgets/base";
import { NextUIProvider } from "@nextui-org/react";
import debounce from "lodash.debounce";
import throttle from "lodash.throttle";
import * as React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { flyTo } from "./actions/fly-to.js";
import {
  useBasemapState,
  useControlsState,
  useLayersState,
  useViewsState,
} from "./hooks/index.js";
import { DEFAULT_MAP_STYLE } from "./model/basemap.js";
import { initParquetWasm } from "./parquet.js";
import DeckFirstRenderer from "./renderers/deck-first.js";
import OverlayRenderer from "./renderers/overlay.js";
import type {
  DeckFirstRendererProps,
  MapRendererProps,
  OverlayRendererProps,
} from "./renderers/types.js";
import SidePanel from "./sidepanel/index";
import { useStore, useViewStateDebounced } from "./state";
import Toolbar from "./toolbar.js";
import { getTooltip } from "./tooltip/index.js";
import type { Message } from "./types.js";
import { isDefined, isGlobeView, sanitizeViewState } from "./util.js";

import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

await initParquetWasm();

function App() {
  // =========================================================================
  // Client-Side State (Zustand)
  // UI-only state that never syncs with Python
  // See: src/state/store.ts
  // =========================================================================

  // Feature highlighting
  const highlightedFeature = useStore((state) => state.highlightedFeature);
  const setHighlightedFeature = useStore(
    (state) => state.setHighlightedFeature,
  );

  // Bounding box selection
  const isDrawingBbox = useStore((state) => state.isDrawingBbox);
  const bboxSelectStart = useStore((state) => state.bboxSelectStart);
  const bboxSelectEnd = useStore((state) => state.bboxSelectEnd);
  const setBboxStart = useStore((state) => state.setBboxStart);
  const setBboxEnd = useStore((state) => state.setBboxEnd);
  const setBboxHover = useStore((state) => state.setBboxHover);

  const isOnMapHoverEventEnabled =
    isDrawingBbox && bboxSelectStart !== undefined;

  const bboxSelectBounds = useMemo(() => {
    if (bboxSelectStart && bboxSelectEnd) {
      const [x0, y0] = bboxSelectStart;
      const [x1, y1] = bboxSelectEnd;
      return [
        Math.min(x0, x1),
        Math.min(y0, y1),
        Math.max(x0, x1),
        Math.max(y0, y1),
      ];
    }
    return null;
  }, [bboxSelectStart, bboxSelectEnd]);

  const bboxSelectPolygonLayer = useMemo(() => {
    if (bboxSelectStart && bboxSelectEnd) {
      const bboxProps: PolygonLayerProps = {
        id: "bbox-select-polygon",
        data: [
          [
            [bboxSelectStart[0], bboxSelectStart[1]],
            [bboxSelectEnd[0], bboxSelectStart[1]],
            [bboxSelectEnd[0], bboxSelectEnd[1]],
            [bboxSelectStart[0], bboxSelectEnd[1]],
          ],
        ],
        getPolygon: (d) => d,
        getFillColor: [0, 0, 0, 50],
        getLineColor: [0, 0, 0, 130],
        stroked: true,
        getLineWidth: 2,
        lineWidthUnits: "pixels",
      };
      if (isDrawingBbox) {
        bboxProps.getFillColor = [255, 255, 0, 120];
        bboxProps.getLineColor = [211, 211, 38, 200];
        bboxProps.getLineWidth = 2;
      }
      return new PolygonLayer(bboxProps);
    }
    return null;
  }, [bboxSelectStart, bboxSelectEnd, isDrawingBbox]);

  const [justClicked, setJustClicked] = useState<boolean>(false);

  const deckRef = useRef<DeckGLRef | null>(null);
  // Expose deck instance on window for debugging
  useEffect(() => {
    if (deckRef.current && typeof window !== "undefined") {
      (window as unknown as Record<string, unknown>).__deck =
        deckRef.current.deck;
    }
  }, [deckRef.current]);

  const model = useModel();

  // ============================================================================
  // Python-Synced State (Backbone models)
  // ============================================================================
  // State that bidirectionally syncs with Python via Jupyter widgets
  // See: src/state/python-sync.ts

  // Map configuration
  const [basemapModelId] = useModelState<string | null>("basemap");
  const [mapHeight] = useModelState<string>("height");
  const [useDevicePixels] = useModelState<number | boolean>(
    "use_device_pixels",
  );
  const [parameters] = useModelState<object>("parameters");

  // UI settings
  const [showTooltip] = useModelState<boolean>("show_tooltip");
  const [showSidePanel] = useModelState<boolean>("show_side_panel");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [customAttribution] = useModelState<string>("custom_attribution");
  const [mapId] = useState(uuidv4());
  const [childLayerIds] = useModelState<string[]>("layers");
  const [viewIds] = useModelState<string | string[] | null>("view");
  const [controlsIds] = useModelState<string[]>("controls");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_selectedBounds, setSelectedBounds] = useModelState<number[] | null>(
    "selected_bounds",
  );

  // initialViewState is the value of view_state on the Python side. This is
  // called `initial` here because it gets passed in to deck's
  // `initialViewState` param, as deck manages its own view state. Further
  // updates to `view_state` from Python are set on the deck `initialViewState`
  // property, which can set new camera state, as described here:
  // https://deck.gl/docs/developer-guide/interactivity
  //
  // `setViewState` is a debounced way to update the model and send view
  // state information back to Python.
  const [initialViewState, setViewState] =
    useViewStateDebounced<MapViewState>("view_state");

  // Handle custom messages
  model.on("msg:custom", (msg: Message) => {
    switch (msg.type) {
      case "fly-to":
        flyTo(msg, setViewState);
        break;

      default:
        break;
    }
  });

  // Fake state just to get react to re-render when a model callback is called
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [stateCounter, setStateCounter] = useState<Date>(new Date());
  const updateStateCallback = () => setStateCounter(new Date());

  const basemapState = useBasemapState(
    basemapModelId,
    model.widget_manager as IWidgetManager,
    updateStateCallback,
  );

  const controls = useControlsState(
    controlsIds,
    model.widget_manager as IWidgetManager,
    updateStateCallback,
  );

  const layers = useLayersState(
    childLayerIds,
    model.widget_manager as IWidgetManager,
    updateStateCallback,
    bboxSelectBounds,
    isDrawingBbox,
    setSelectedBounds,
  );

  const views = useViewsState(
    viewIds,
    model.widget_manager as IWidgetManager,
    updateStateCallback,
  );

  const onMapClickHandler = useCallback(
    (info: PickingInfo) => {
      // We added this flag to prevent the hover event from firing after a
      // click event.
      if (typeof info.coordinate !== "undefined") {
        if (model.get("_has_click_handlers")) {
          model.send({ kind: "on-click", coordinate: info.coordinate });
        }
      }
      setJustClicked(true);

      const clickedObject = info.object;
      if (typeof clickedObject !== "undefined") {
        setHighlightedFeature(info as GeoArrowPickingInfo);
      } else {
        setHighlightedFeature(undefined);
      }

      if (isDrawingBbox && info.coordinate) {
        if (bboxSelectStart === undefined) {
          setBboxStart(info.coordinate);
        } else {
          setBboxEnd(info.coordinate);
        }
      }

      setTimeout(() => {
        setJustClicked(false);
      }, 100);
    },
    [
      setHighlightedFeature,
      isDrawingBbox,
      bboxSelectStart,
      setBboxStart,
      setBboxEnd,
    ],
  );

  const onMapHoverHandler = useCallback(
    throttle((info: PickingInfo) => {
      if (isOnMapHoverEventEnabled && !justClicked && info.coordinate) {
        setBboxHover(info.coordinate);
      }
    }, 100),
    [isOnMapHoverEventEnabled, justClicked, setBboxHover],
  );

  const mapRenderProps: MapRendererProps = {
    mapStyle: basemapState?.style || DEFAULT_MAP_STYLE,
    customAttribution,
    deckRef,
    initialViewState,
    layers: bboxSelectPolygonLayer
      ? layers.concat(bboxSelectPolygonLayer)
      : layers,
    getTooltip: (showTooltip && getTooltip) || undefined,
    getCursor: () => (isDrawingBbox ? "crosshair" : "grab"),
    pickingRadius: pickingRadius,
    onClick: onMapClickHandler,
    onHover: onMapHoverHandler,
    ...(isDefined(useDevicePixels) && { useDevicePixels }),
    // This is a hack to force a react re-render when the canvas is resized
    // https://github.com/developmentseed/lonboard/issues/994
    // until the upstream is resolved:
    // https://github.com/visgl/deck.gl/issues/9666
    onResize: debounce(updateStateCallback, 100),
    onViewStateChange: (event) => {
      setViewState(sanitizeViewState(views, event.viewState));
    },
    parameters: parameters || {},
    views,
    controls,
  };

  const overlayRenderProps: OverlayRendererProps = {
    interleaved: basemapState?.mode === "interleaved",
  };

  const deckFirstRenderProps: DeckFirstRendererProps = {
    renderBasemap: Boolean(basemapState),
  };

  return (
    <div
      className="lonboard"
      style={{ minHeight: "100%", height: mapHeight }}
      // This attribute suppresses the context menu on right click in JupyterLab
      // https://jupyterlab.readthedocs.io/en/latest/extension/extension_points.html#context-menu
      // https://jupyter.zulipchat.com/#narrow/channel/471314-geojupyter/topic/Possible.20to.20disable.20JupyterLab.20popup.20on.20right.20click.3F/near/541082696
      data-jp-suppress-context-menu
    >
      <div
        id={`map-${mapId}`}
        className="flex"
        style={{
          width: "100%",
          height: "100%",
          // Use a dark background when in globe view so the globe is easier to
          // delineate
          // In the future we may want to allow the user to customize this
          ...(isGlobeView(views) && {
            background: "linear-gradient(0, #000, #223)",
          }),
        }}
      >
        <Toolbar />

        {showSidePanel && highlightedFeature && (
          <SidePanel
            info={highlightedFeature}
            onClose={() => setHighlightedFeature(undefined)}
          />
        )}
        <div className="bg-transparent h-full w-full relative">
          {basemapState?.mode === "overlaid" ||
          basemapState?.mode === "interleaved" ? (
            <OverlayRenderer {...mapRenderProps} {...overlayRenderProps} />
          ) : (
            <DeckFirstRenderer {...mapRenderProps} {...deckFirstRenderProps} />
          )}
        </div>
      </div>
    </div>
  );
}

const WrappedApp = () => (
  <NextUIProvider>
    <App />
  </NextUIProvider>
);

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(WrappedApp),
};

export default module;

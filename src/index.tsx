import { createRender, useModel, useModelState } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import { MapViewState, PickingInfo } from "@deck.gl/core";
import { DeckGLRef } from "@deck.gl/react";
import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import { NextUIProvider } from "@nextui-org/react";
import throttle from "lodash.throttle";
import * as React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { flyTo } from "./actions/fly-to.js";
import { DEFAULT_MAP_STYLE, MaplibreBasemapModel } from "./model/basemap.js";
import {
  initializeLayer,
  type BaseLayerModel,
  initializeChildModels,
} from "./model/index.js";
import { loadModel } from "./model/initialize.js";
import { BaseViewModel, initializeView } from "./model/view.js";
import { initParquetWasm } from "./parquet.js";
import DeckFirstRenderer from "./renderers/deck-first.js";
import OverlayRenderer from "./renderers/overlay.js";
import {
  DeckFirstRendererProps,
  MapRendererProps,
  OverlayRendererProps,
} from "./renderers/types.js";
import SidePanel from "./sidepanel/index";
import { useViewStateDebounced } from "./state";
import Toolbar from "./toolbar.js";
import { getTooltip } from "./tooltip/index.js";
import { Message } from "./types.js";
import { isDefined, isGlobeView } from "./util.js";
import { MachineContext, MachineProvider } from "./xstate";
import * as selectors from "./xstate/selectors";

import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

await initParquetWasm();

const DEFAULT_INITIAL_VIEW_STATE = {
  latitude: 10,
  longitude: 0,
  zoom: 0.5,
  bearing: 0,
  pitch: 0,
};

function App() {
  const actorRef = MachineContext.useActorRef();
  const isDrawingBBoxSelection = MachineContext.useSelector(
    selectors.isDrawingBBoxSelection,
  );
  const isOnMapHoverEventEnabled = MachineContext.useSelector(
    selectors.isOnMapHoverEventEnabled,
  );

  const highlightedFeature = MachineContext.useSelector(
    (s) => s.context.highlightedFeature,
  );

  const bboxSelectPolygonLayer = MachineContext.useSelector(
    selectors.getBboxSelectPolygonLayer,
  );
  const bboxSelectBounds = MachineContext.useSelector(
    selectors.getBboxSelectBounds,
  );

  const [justClicked, setJustClicked] = useState<boolean>(false);

  // Expose DeckGL instance on window for Playwright e2e tests
  const deckRef = useRef<DeckGLRef | null>(null);
  useEffect(() => {
    if (deckRef.current && typeof window !== "undefined") {
      (window as unknown as Record<string, unknown>).__deck =
        deckRef.current.deck;
    }
  }, [deckRef.current]);

  const model = useModel();

  const [basemapModelId] = useModelState<string | null>("basemap");
  const [mapHeight] = useModelState<string>("height");
  const [showTooltip] = useModelState<boolean>("show_tooltip");
  const [showSidePanel] = useModelState<boolean>("show_side_panel");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [useDevicePixels] = useModelState<number | boolean>(
    "use_device_pixels",
  );
  const [parameters] = useModelState<object>("parameters");
  const [customAttribution] = useModelState<string>("custom_attribution");
  const [mapId] = useState(uuidv4());
  const [childLayerIds] = useModelState<string[]>("layers");
  const [viewIds] = useModelState<string | string[]>("views");

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

  //////////////////////
  // Basemap state
  //////////////////////

  const [basemapState, setBasemapState] = useState<MaplibreBasemapModel | null>(
    null,
  );

  useEffect(() => {
    const loadBasemap = async () => {
      try {
        if (!basemapModelId) {
          setBasemapState(null);
          return;
        }

        const basemapModel = await loadModel(
          model.widget_manager as IWidgetManager,
          basemapModelId,
        );
        const basemap = new MaplibreBasemapModel(
          basemapModel,
          updateStateCallback,
        );
        setBasemapState(basemap);
      } catch (error) {
        console.error("Error loading basemap model:", error);
      }
    };

    loadBasemap();
  }, [basemapModelId]);

  //////////////////////
  // Layers state
  //////////////////////

  const [layersState, setLayersState] = useState<
    Record<string, BaseLayerModel>
  >({});

  useEffect(() => {
    const loadAndUpdateLayers = async () => {
      try {
        const layerModels = await initializeChildModels<BaseLayerModel>(
          model.widget_manager as IWidgetManager,
          childLayerIds,
          layersState,
          async (model: WidgetModel) =>
            initializeLayer(model, updateStateCallback),
        );

        setLayersState(layerModels);

        if (!isDrawingBBoxSelection) {
          // Note: selected_bounds is a property of the **Map**. In the future,
          // when we use deck.gl to perform picking, we'll have
          // `selected_indices` as a property of each individual layer.
          model.set("selected_bounds", bboxSelectBounds);
          model.save_changes();
          // childModels.forEach((layer) => {
          //   layer.set("selected_bounds", bboxSelectBounds);
          //   layer.save_changes();
          // });
        }
      } catch (error) {
        console.error("Error loading child models or setting bounds:", error);
      }
    };

    loadAndUpdateLayers();
  }, [childLayerIds, bboxSelectBounds, isDrawingBBoxSelection]);

  const layers = Object.values(layersState).flatMap((layerModel) =>
    layerModel.render(),
  );

  //////////////////////
  // Views state
  //////////////////////

  const [viewsState, setViewsState] = useState<
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    Record<string, BaseViewModel<any>>
  >({});

  useEffect(() => {
    const loadAndUpdateViews = async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const viewsModels = await initializeChildModels<BaseViewModel<any>>(
          model.widget_manager as IWidgetManager,
          typeof viewIds === "string" ? [viewIds] : viewIds,
          viewsState,
          async (model: WidgetModel) =>
            initializeView(model, updateStateCallback),
        );

        setViewsState(viewsModels);
      } catch (error) {
        console.error("Error loading child views:", error);
      }
    };

    loadAndUpdateViews();
  }, [viewIds]);

  const views = Object.values(viewsState).map((viewModel) => viewModel.build());

  const onMapClickHandler = useCallback((info: PickingInfo) => {
    // We added this flag to prevent the hover event from firing after a
    // click event.
    if (typeof info.coordinate !== "undefined") {
      if (model.get("_has_click_handlers")) {
        model.send({ kind: "on-click", coordinate: info.coordinate });
      }
    }
    setJustClicked(true);
    actorRef.send({
      type: "Map click event",
      data: info,
    });
    setTimeout(() => {
      setJustClicked(false);
    }, 100);
  }, []);

  const onMapHoverHandler = useCallback(
    throttle(
      (info: PickingInfo) =>
        isOnMapHoverEventEnabled &&
        !justClicked &&
        actorRef.send({
          type: "Map hover event",
          data: info,
        }),
      100,
    ),
    [isOnMapHoverEventEnabled, justClicked],
  );

  const mapRenderProps: MapRendererProps = {
    mapStyle: basemapState?.style || DEFAULT_MAP_STYLE,
    customAttribution,
    deckRef,
    initialViewState: ["longitude", "latitude", "zoom"].every((key) =>
      Object.keys(initialViewState).includes(key),
    )
      ? initialViewState
      : DEFAULT_INITIAL_VIEW_STATE,
    layers: bboxSelectPolygonLayer
      ? layers.concat(bboxSelectPolygonLayer)
      : layers,
    getTooltip: (showTooltip && getTooltip) || undefined,
    getCursor: () => (isDrawingBBoxSelection ? "crosshair" : "grab"),
    pickingRadius: pickingRadius,
    onClick: onMapClickHandler,
    onHover: onMapHoverHandler,
    // @ts-expect-error useDevicePixels should allow number
    // https://github.com/visgl/deck.gl/pull/9826
    useDevicePixels: isDefined(useDevicePixels) ? useDevicePixels : true,
    onViewStateChange: (event) => {
      const { viewState } = event;

      // This condition is necessary to confirm that the viewState is
      // of type MapViewState.
      if ("latitude" in viewState) {
        const { longitude, latitude, zoom, pitch, bearing } = viewState;
        setViewState({
          longitude,
          latitude,
          zoom,
          pitch,
          bearing,
        });
      }
    },
    parameters: parameters || {},
    views,
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
          ...(isGlobeView(views) && {
            background: "linear-gradient(0, #000, #223)",
          }),
        }}
      >
        <Toolbar />

        {showSidePanel && highlightedFeature && (
          <SidePanel
            info={highlightedFeature}
            onClose={() => actorRef.send({ type: "Close side panel" })}
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
    <MachineProvider>
      <App />
    </MachineProvider>
  </NextUIProvider>
);

const module: { render: Render; initialize?: Initialize } = {
  render: createRender(WrappedApp),
};

export default module;

import * as React from "react";
import { useState } from "react";
import { createRender, useModelState } from "@anywidget/react";
import type { Initialize, Render } from "@anywidget/types";
import { initParquetWasm } from "./parquet.js";
import { v4 as uuidv4 } from "uuid";

import { MachineContext, MachineProvider } from "./xstate";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import { NextUIProvider } from "@nextui-org/react";
import Toolbar from "./toolbar.js";
import SidePanel from "./sidepanel/index";
import { MaplibreRenderer } from "./renderers/MaplibreRenderer.js";
import { DeckGLRenderer } from "./renderers/DeckGLRenderer.js";
import type { RendererProps } from "./types/rendererProps.js";

await initParquetWasm();

type RenderMode = "maplibre-child" | "deckgl-child";

function App() {
  const actorRef = MachineContext.useActorRef();
  const highlightedFeature = MachineContext.useSelector(
    (s: any) => s.context.highlightedFeature,
  );

  const [mapHeight] = useModelState<string>("height");
  const [showSidePanel] = useModelState<boolean>("show_side_panel");
  const [renderMode] = useModelState<RenderMode>("render_mode");
  const [mapStyle] = useModelState<string>("basemap_style");
  const [showTooltip] = useModelState<boolean>("show_tooltip");
  const [pickingRadius] = useModelState<number>("picking_radius");
  const [useDevicePixels] = useModelState<number | boolean>("use_device_pixels");
  const [parameters] = useModelState<object>("parameters");
  const [customAttribution] = useModelState<string>("custom_attribution");

  const [mapId] = useState(uuidv4());

  const rendererProps: RendererProps = {
    mapStyle: mapStyle || "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json",
    showTooltip: showTooltip || false,
    pickingRadius: pickingRadius || 0,
    useDevicePixels: useDevicePixels ?? true,
    parameters: parameters || {},
    customAttribution: customAttribution || "",
  };

  const MapRenderer = renderMode === "deckgl-child" ? DeckGLRenderer : MaplibreRenderer;

  return (
    <div className="lonboard" style={{ minHeight: "100%", height: mapHeight }}>
      <div
        id={`map-${mapId}`}
        className="flex"
        style={{ width: "100%", height: "100%" }}
      >
        <Toolbar />

        {showSidePanel && highlightedFeature && (
          <SidePanel
            info={highlightedFeature}
            onClose={() => actorRef.send({ type: "Close side panel" })}
          />
        )}
        <div className="bg-red-800 h-full w-full relative">
          <MapRenderer {...rendererProps} />
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

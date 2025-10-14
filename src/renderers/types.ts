import { MapViewState, PickingInfo, type Layer } from "@deck.gl/core";
import { DeckGLRef } from "@deck.gl/react";
import type { RefObject } from "react";

export interface MapRendererProps {
  mapStyle: string;
  customAttribution: string;
  initialViewState: MapViewState;
  layers: Layer[];
  deckRef?: RefObject<DeckGLRef | null>;
  showTooltip: boolean;
  getTooltip?: ((info: PickingInfo) => string | null) | undefined;
  isDrawingBBoxSelection: boolean;
  pickingRadius: number;
  useDevicePixels: number | boolean;
  parameters: object;
  onMapClick: (info: PickingInfo) => void;
  onMapHover: (info: PickingInfo) => void;
  onViewStateChange: (event: { viewState: MapViewState }) => void;
}

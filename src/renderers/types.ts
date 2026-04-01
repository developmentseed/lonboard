import type { DeckProps, MapViewState, View } from "@deck.gl/core";
import type { DeckGLRef } from "@deck.gl/react";
import type { RefObject } from "react";

import type { BaseMapControlModel } from "../model";
import type { FlyToMessage } from "../types";

export type RendererRef = {
  flyTo: (msg: FlyToMessage) => void;
};

type ViewOrViews = View | View[];
export type MapRendererProps<ViewsT extends ViewOrViews = ViewOrViews> = Pick<
  DeckProps<ViewsT>,
  | "getCursor"
  | "getTooltip"
  | "initialViewState"
  | "layers"
  | "onClick"
  | "onHover"
  | "onResize"
  | "onViewStateChange"
  | "parameters"
  | "pickingRadius"
  | "useDevicePixels"
  | "views"
> & {
  mapStyle: string;
  customAttribution: string;
  deckRef?: RefObject<DeckGLRef | null>;
  controls: BaseMapControlModel[];
};

export type OverlayRendererProps = {
  interleaved: boolean;
};

export type DeckFirstRendererProps = {
  renderBasemap: boolean;
  setViewState: (viewState: MapViewState) => void;
};

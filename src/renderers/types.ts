import type { DeckProps, View } from "@deck.gl/core";
import type { DeckGLRef } from "@deck.gl/react";
import type { RefObject } from "react";

type ViewOrViews = View | View[] | null;
export type MapRendererProps<ViewsT extends ViewOrViews = null> = Pick<
  DeckProps<ViewsT>,
  | "getCursor"
  | "getTooltip"
  | "initialViewState"
  | "layers"
  | "onClick"
  | "onHover"
  | "onViewStateChange"
  | "parameters"
  | "pickingRadius"
  | "useDevicePixels"
> & {
  mapStyle: string;
  customAttribution: string;
  deckRef?: RefObject<DeckGLRef | null>;
};

export type OverlayRendererProps = {
  interleaved: boolean;
};

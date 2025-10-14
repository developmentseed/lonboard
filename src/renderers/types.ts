import type { DeckProps, View } from "@deck.gl/core";
import type { DeckGLRef } from "@deck.gl/react";
import type { RefObject } from "react";

type ViewOrViews = View | View[] | null;
export type MapRendererProps<ViewsT extends ViewOrViews = null> = Pick<
  DeckProps<ViewsT>,
  | "layers"
  | "getTooltip"
  | "getCursor"
  | "pickingRadius"
  | "useDevicePixels"
  | "parameters"
  | "initialViewState"
  | "onClick"
  | "onHover"
  | "onViewStateChange"
> & {
  mapStyle: string;
  customAttribution: string;
  deckRef?: RefObject<DeckGLRef | null>;
};

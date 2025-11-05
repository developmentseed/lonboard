import type { DeckProps, View } from "@deck.gl/core";
import type { DeckGLRef } from "@deck.gl/react";
import type { RefObject } from "react";

import type { BaseMapControlModel } from "../model";

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
};

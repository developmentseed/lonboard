import type { WidgetModel } from "@jupyter-widgets/base";

import { BaseModel } from "./base";

export const DEFAULT_MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json";

export class MaplibreBasemapModel extends BaseModel {
  mode?: "interleaved" | "overlaid" | "reverse-controlled";
  style?: string;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("mode", "mode");
    this.initRegularAttribute("style", "style");
  }
}

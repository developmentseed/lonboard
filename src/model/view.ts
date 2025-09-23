import { _GlobeView as GlobeView, GlobeViewProps } from "@deck.gl/core";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined } from "../util.js";
import { BaseModel } from "./base.js";

export class GlobeViewModel extends BaseModel {
  protected resolution: GlobeViewProps["resolution"];
  protected nearZMultiplier: GlobeViewProps["nearZMultiplier"];
  protected farZMultiplier: GlobeViewProps["farZMultiplier"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("resolution", "resolution");
    this.initRegularAttribute("near_z_multiplier", "nearZMultiplier");
    this.initRegularAttribute("far_z_multiplier", "farZMultiplier");
  }

  viewProps(): GlobeViewProps {
    return {
      ...(isDefined(this.resolution) && { resolution: this.resolution }),
      ...(isDefined(this.nearZMultiplier) && {
        nearZMultiplier: this.nearZMultiplier,
      }),
      ...(isDefined(this.farZMultiplier) && {
        farZMultiplier: this.farZMultiplier,
      }),
    };
  }

  render(): GlobeView {
    return new GlobeView(this.viewProps());
  }
}

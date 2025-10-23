import {
  CompassWidget,
  FullscreenWidget,
  _ScaleWidget as ScaleWidget,
  ZoomWidget,
} from "@deck.gl/react";
import type { WidgetModel } from "@jupyter-widgets/base";
import React from "react";
import {
  FullscreenControl,
  NavigationControl,
  ScaleControl,
} from "react-map-gl/maplibre";

import { isDefined } from "../util";
import { BaseModel } from "./base";

export abstract class BaseMapControlModel extends BaseModel {
  static controlType: string;

  protected position?:
    | "top-left"
    | "top-right"
    | "bottom-left"
    | "bottom-right";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("position", "position");
  }

  baseDeckProps() {
    return {
      ...(isDefined(this.position) ? { placement: this.position } : {}),
    };
  }

  baseMaplibreProps() {
    return {
      ...(isDefined(this.position) ? { position: this.position } : {}),
    };
  }

  abstract renderDeck(): React.JSX.Element | null;
  abstract renderMaplibre(): React.JSX.Element | null;
}

export class FullscreenControlModel extends BaseMapControlModel {
  static controlType = "fullscreen";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
  }

  renderDeck() {
    const { placement, ...otherProps } = this.baseDeckProps();
    const props = { placement: placement || "top-right", ...otherProps };
    console.log(placement);
    return <div>{<FullscreenWidget {...props} />}</div>;
  }

  renderMaplibre() {
    return <div>{<FullscreenControl {...this.baseMaplibreProps()} />}</div>;
  }
}

export class NavigationControlModel extends BaseMapControlModel {
  static controlType = "navigation";

  protected showCompass?: boolean;
  protected showZoom?: boolean;
  protected visualizePitch?: boolean;
  protected visualizeRoll?: boolean;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("show_compass", "showCompass");
    this.initRegularAttribute("show_zoom", "showZoom");
    this.initRegularAttribute("visualize_pitch", "visualizePitch");
    this.initRegularAttribute("visualize_roll", "visualizeRoll");
  }

  renderDeck() {
    return (
      <div>
        {this.showZoom && <ZoomWidget {...this.baseDeckProps()} />}
        {this.showCompass && <CompassWidget {...this.baseDeckProps()} />}
      </div>
    );
  }

  renderMaplibre() {
    const props = {
      ...this.baseMaplibreProps(),
      ...(isDefined(this.showCompass) && { showCompass: this.showCompass }),
      ...(isDefined(this.showZoom) && { showZoom: this.showZoom }),
      ...(isDefined(this.visualizePitch) && {
        visualizePitch: this.visualizePitch,
      }),
      ...(isDefined(this.visualizeRoll) && {
        visualizeRoll: this.visualizeRoll,
      }),
    };
    return <NavigationControl {...props} />;
  }
}

export class ScaleControlModel extends BaseMapControlModel {
  static controlType = "scale";

  protected maxWidth?: number;
  protected unit?: "imperial" | "metric" | "nautical";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("max_width", "maxWidth");
    this.initRegularAttribute("unit", "unit");
  }

  renderDeck() {
    return <ScaleWidget {...this.baseDeckProps()} />;
  }

  renderMaplibre() {
    const props = {
      ...this.baseMaplibreProps(),
      ...(isDefined(this.maxWidth) && { maxWidth: this.maxWidth }),
      ...(isDefined(this.unit) && { unit: this.unit }),
    };
    return <div>{<ScaleControl {...props} />}</div>;
  }
}

export async function initializeControl(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseMapControlModel> {
  const controlType = model.get("_control_type");
  let controlModel: BaseMapControlModel;
  switch (controlType) {
    case FullscreenControlModel.controlType:
      controlModel = new FullscreenControlModel(model, updateStateCallback);
      break;

    case NavigationControlModel.controlType:
      controlModel = new NavigationControlModel(model, updateStateCallback);
      break;

    case ScaleControlModel.controlType:
      controlModel = new ScaleControlModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no control supported for ${controlType}`);
  }

  return controlModel;
}

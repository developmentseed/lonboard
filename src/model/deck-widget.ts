import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./base.js";
import { Widget, WidgetPlacement } from "@deck.gl/core";
import { CompassWidget, ZoomWidget, FullscreenWidget } from '@deck.gl/widgets'

export abstract class BaseDeckWidgetModel extends BaseModel {

  protected viewId: string | null = null;
  protected placement: WidgetPlacement = "top-left";
  protected props: Object = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("props", "props");
    this.initRegularAttribute("view_id", "viewId");
    this.initRegularAttribute("placement", "placement");
  }

  abstract render(): Widget;
}

export class FullscreenWidgetModel extends BaseDeckWidgetModel {
  static widgetType = "fullscreen";

  protected enterLabel: string = "Enter Fullscreen";
  protected exitLabel: string = "Exit Fullscreen";
  protected style: Partial<CSSStyleDeclaration> = {};
  protected className: string | undefined = undefined;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("enter_label", "enterLabel");
    this.initRegularAttribute("exit_label", "exitLabel");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): FullscreenWidget {
    return new FullscreenWidget({
      id: "fullscreen",
      placement: this.placement,
      enterLabel: this.enterLabel,
      exitLabel: this.exitLabel,
      style: this.style,
      className: this.className,
    }) 
  }
}

export async function initializeWidget(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseDeckWidgetModel> {
  const deckWidgetType = model.get("_widget_type");
  let deckWidgetModel: BaseDeckWidgetModel;
  switch (deckWidgetType) {
    case FullscreenWidgetModel.widgetType:
      deckWidgetModel = new FullscreenWidgetModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no layer supported for ${deckWidgetType}`);
  }
  
  return deckWidgetModel;
}

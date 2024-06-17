import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./base.js";
import { Widget, WidgetPlacement } from "@deck.gl/core";
import { CompassWidget, ZoomWidget, FullscreenWidget, LightTheme } from "@deck.gl/widgets";
import { LegendWidget, NorthArrowWidget, TitleWidget, ScaleWidget, SaveImageWidget } from "./deck-widget.js";

export abstract class BaseDeckWidgetModel extends BaseModel {

  // protected props: Object = {};
  // protected viewId: string | null = null;
  protected placement: WidgetPlacement = "top-left";
  protected className: string | undefined = undefined;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    // this.initRegularAttribute("props", "props");
    // this.initRegularAttribute("view_id", "viewId");
    this.initRegularAttribute("placement", "placement");
    this.initRegularAttribute("class_name", "className");
  }

  abstract render(): Widget;
}

export class FullscreenWidgetModel extends BaseDeckWidgetModel {
  static widgetType = "fullscreen";

  protected enterLabel: string = "Enter Fullscreen";
  protected exitLabel: string = "Exit Fullscreen";
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("enter_label", "enterLabel");
    this.initRegularAttribute("exit_label", "exitLabel");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): FullscreenWidget {
    return new FullscreenWidget({
      id: "fullscreen-widget",
      placement: this.placement,
      enterLabel: this.enterLabel,
      exitLabel: this.exitLabel,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style,
      },
      className: this.className,
    }) 
  }
}

export class ZoomWidgetModel extends BaseDeckWidgetModel {
  static widgetType = "zoom";

  protected zoomInLabel: string = "Zoom In";
  protected zoomOutLabel: string = "Zoom Out";
  protected transitionDuration: number = 200;
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("zoom_in_label", "zoomInLabel");
    this.initRegularAttribute("zoom_out_label", "zoomOutLabel");
    this.initRegularAttribute("transition_duration", "transitionDuration");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): ZoomWidget {
    return new ZoomWidget({
      id: "zoom-widget",
      placement: this.placement,
      zoomInLabel: this.zoomInLabel,
      zoomOutLabel: this.zoomOutLabel,
      transitionDuration: this.transitionDuration,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style,
      },
      className: this.className,
    }) 
  }
}

export class CompassWidgetModel extends BaseDeckWidgetModel {
  static widgetType = "compass";

  protected label: string = "Compass";
  protected transitionDuration: number = 200;
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("label", "label");
    this.initRegularAttribute("transition_duration", "transitionDuration");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): CompassWidget {
    return new CompassWidget({
      id: "compass-widget",
      placement: this.placement,
      label: this.label,
      transitionDuration: this.transitionDuration,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style,
      },
      className: this.className,
    }) 
  }
}

export class NorthArrowWidgetModel extends BaseDeckWidgetModel {
  static widgetType = "north-arrow";

  protected label: string = "North Arrow";
  protected transitionDuration: number = 200;
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("label", "label");
    this.initRegularAttribute("transition_duration", "transitionDuration");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): NorthArrowWidget {
    return new NorthArrowWidget({
      id: "north-arrow-widget",
      placement: this.placement,
      label: this.label,
      transitionDuration: this.transitionDuration,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style,
      },
      className: this.className,
    }) 
  }
}

export class TitleWidgetModel extends BaseDeckWidgetModel{
  static widgetType = "title";

  protected title: string = "";
  protected placement: WidgetPlacement = "top-right";
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("title", "title");
    this.initRegularAttribute("placement", "placement");
    this.initRegularAttribute("style", "style");
  }

  render() {
    return new TitleWidget({
      id:  "title", 
      title: this.title, 
      placement: this.placement, 
      style: {
        ...LightTheme,
        ...this.style,
      },
      className: this.className,
    })
  }
}

export class LegendWidgetModel extends BaseDeckWidgetModel{
  static widgetType = "legend";

  protected title: string = "Legend";
  protected labels: string[] = [];
  protected colors: string[] = [];
  protected placement: WidgetPlacement = "bottom-right";
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("title", "title");
    this.initRegularAttribute("placement", "placement");
    this.initRegularAttribute("style", "style");

    this.initRegularAttribute("labels", "labels");
    this.initRegularAttribute("colors", "colors");
  }

  render() {
    const legend = new Map<string,string>()
    for (const i in this.labels) {
      legend.set(this.labels[i], this.colors[i]);
    }

    return new LegendWidget({
      id:  "legend", 
      title: this.title, 
      legend: legend,
      placement: this.placement, 
      style: {
        // ...LightTheme,
        ...this.style,
      },
      className: this.className,
    })
  }
}

export class ScaleWidgetModel extends BaseDeckWidgetModel{
  static widgetType = "scale";

  protected placement: WidgetPlacement = "bottom-left";
  protected style: Partial<CSSStyleDeclaration> = {};
  protected maxWidth: number = 300;
  protected useImperial: boolean = false;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("placement", "placement");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("max_width", "maxWidth");
    this.initRegularAttribute("use_imperial", "useImperial");
  }

  render() {
    return new ScaleWidget({
      id:  "scale", 
      placement: this.placement, 
      style: {
        // ...LightTheme,
        ...this.style,
      },
      maxWidth: this.maxWidth,
      useImperial: this.useImperial,
      className: this.className,
    })
  }
}

export class SaveImageWidgetModel extends BaseDeckWidgetModel{
  static widgetType = "save-image";

  protected label: string = "";
  protected placement: WidgetPlacement = "top-right";
  protected style: Partial<CSSStyleDeclaration> = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("label", "label");
    this.initRegularAttribute("placement", "placement");
    this.initRegularAttribute("style", "style");
  }

  render() {
    return new SaveImageWidget({
      id:  "title", 
      label: this.label, 
      placement: this.placement, 
      style: {
        ...LightTheme,
        ...this.style,
      },
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

    case ZoomWidgetModel.widgetType:
      deckWidgetModel = new ZoomWidgetModel(model, updateStateCallback);
      break;

    case CompassWidgetModel.widgetType:
      deckWidgetModel = new CompassWidgetModel(model, updateStateCallback);
      break;

    case TitleWidgetModel.widgetType:
      deckWidgetModel = new TitleWidgetModel(model, updateStateCallback);
      break;

    case NorthArrowWidgetModel.widgetType:
      deckWidgetModel = new NorthArrowWidgetModel(model, updateStateCallback);
      break;  

    case LegendWidgetModel.widgetType:
      deckWidgetModel = new LegendWidgetModel(model, updateStateCallback);
      break;  

    case ScaleWidgetModel.widgetType:
      deckWidgetModel = new ScaleWidgetModel(model, updateStateCallback);
      break;
      
    case SaveImageWidgetModel.widgetType:
        deckWidgetModel = new SaveImageWidgetModel(model, updateStateCallback);
        break;  

    default:
      throw new Error(`no widget supported for ${deckWidgetType}`);
  }
  return deckWidgetModel;
}

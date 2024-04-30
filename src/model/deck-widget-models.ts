import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./base.js";
import { Widget, WidgetPlacement } from "@deck.gl/core";
import { CompassWidget, ZoomWidget, FullscreenWidget, LightTheme } from "@deck.gl/widgets";
import { TitleWidget } from "./deck-widget.js";

export abstract class BaseDeckWidgetModel extends BaseModel {

  // protected viewId: string | null = null;
  protected placement: WidgetPlacement = "top-left";
  // protected props: Object = {};

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    // this.initRegularAttribute("props", "props");
    // this.initRegularAttribute("view_id", "viewId");
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
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style
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
  protected className: string | undefined = undefined;

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
      id: "fullscreen",
      placement: this.placement,
      zoomInLabel: this.zoomInLabel,
      zoomOutLabel: this.zoomOutLabel,
      transitionDuration: this.transitionDuration,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style
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
  protected className: string | undefined = undefined;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("label", "label");
    this.initRegularAttribute("transition_duration", "transitionDuration");
    this.initRegularAttribute("style", "style");
    this.initRegularAttribute("class_name", "className");
  }

  render(): CompassWidget {
    return new CompassWidget({
      id: "fullscreen",
      label: this.label,
      transitionDuration: this.transitionDuration,
      style: {
        ...LightTheme as Partial<CSSStyleDeclaration>,
        ...this.style
      },
      className: this.className,
    }) 
  }
}

export class TitleWidgetModel extends BaseDeckWidgetModel{
  static widgetType = "title";

  protected title: string = "";
  protected placement: WidgetPlacement = "top-right";
  //protected style: Partial<CSSStyleDeclaration> = {};

  protected fontSize: string = "";
  protected fontStyle: string = "";
  protected fontFamily: string = "";
  protected color: string = "";
  protected backgroundColor: string = "";
  protected outline: string = "";
  protected borderRadius: string = "";
  protected border: string = "";
  protected padding: string = "";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("title", "title");
    this.initRegularAttribute("placement", "placement");
    //this.initRegularAttribute("style", "style");

    this.initRegularAttribute("font_size", "fontSize" );
    this.initRegularAttribute("font_style", "fontStyle" );
    this.initRegularAttribute("font_family", "fontFamily" );
    this.initRegularAttribute("font_color", "color" );
    this.initRegularAttribute("background_color", "backgroundColor" );
    this.initRegularAttribute("outline", "outline" );
    this.initRegularAttribute("border_radius", "borderRadius" );
    this.initRegularAttribute("border", "border" );
    this.initRegularAttribute("padding", "padding" );
    
  }

  render() {
    return new TitleWidget({
      id:  "title", 
      title: this.title, 
      placement: this.placement, 
      style: {
        ...LightTheme,
        'fontSize': this.fontSize,
        'fontStyle': this.fontStyle,
        'fontFamily': this.fontFamily,
        'color': this.color,
        'backgroundColor': this.backgroundColor,
        'outline': this.outline,
        'borderRadius': this.borderRadius,
        'border': this.border,
        'padding': this.padding,
      }
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

    default:
      throw new Error(`no widget supported for ${deckWidgetType}`);
  }
  
  return deckWidgetModel;
}

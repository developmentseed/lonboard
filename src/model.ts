import {
  GeoArrowPathLayer,
  GeoArrowPathLayerProps,
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
  GeoArrowSolidPolygonLayer,
  GeoArrowSolidPolygonLayerProps,
} from "@geoarrow/deck.gl-layers";
import * as arrow from "apache-arrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import type { Layer, LayerExtension, LayerProps } from "@deck.gl/core/typed";
import { parseParquetBuffers } from "./parquet";
import { parseAccessor } from "./accessor";
import { BaseExtensionModel, initializeExtension } from "./extensions";
import { loadChildModels } from "./util";

export abstract class BaseModel {
  protected model: WidgetModel;
  protected callbacks: Map<string, () => void>;
  protected updateStateCallback: () => void;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    this.model = model;
    this.model.on("change", updateStateCallback);
    this.updateStateCallback = updateStateCallback;
    this.callbacks = new Map();
    this.callbacks.set("change", updateStateCallback);
  }

  async loadSubModels() {
    return;
  }

  /**
   * Initialize an attribute that does not need any transformation from its
   * serialized representation to its deck.gl representation.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  protected initRegularAttribute(pythonName: string, jsName: string) {
    this[jsName] = this.model.get(pythonName);

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = this.model.get(pythonName);
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
  }

  /**
   * Initialize an accessor that can either be a scalar JSON value or a Parquet
   * table with a single column, intended to be passed in as an Arrow Vector.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  protected initVectorizedAccessor(pythonName: string, jsName: string) {
    this[jsName] = parseAccessor(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = parseAccessor(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
  }

  /**
   * Finalize any resources held by the model
   */
  finalize(): void {
    for (const [changeKey, callback] of Object.entries(this.callbacks)) {
      this.model.off(changeKey, callback);
    }
  }
}

export abstract class BaseLayerModel extends BaseModel {
  protected table: arrow.Table;

  protected pickable: LayerProps["pickable"];
  protected visible: LayerProps["visible"];
  protected opacity: LayerProps["opacity"];
  protected autoHighlight: LayerProps["autoHighlight"];

  protected extensions: BaseExtensionModel[];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table", "table");

    this.initRegularAttribute("pickable", "pickable");
    this.initRegularAttribute("visible", "visible");
    this.initRegularAttribute("opacity", "opacity");
    this.initRegularAttribute("auto_highlight", "autoHighlight");
  }

  async loadSubModels() {
    await this.initLayerExtensions();
  }

  extensionInstances(): LayerExtension[] {
    return this.extensions.map((extension) => extension.extensionInstance);
  }

  extensionProps() {
    let props = {};
    for (const extension of this.extensions) {
      props = { ...props, ...extension.extensionProps() };
    }
    return props;
  }

  baseLayerProps(): LayerProps {
    return {
      extensions: this.extensionInstances(),
      ...this.extensionProps(),
      id: this.model.model_id,
      pickable: this.pickable,
      visible: this.visible,
      opacity: this.opacity,
      autoHighlight: this.autoHighlight,
    };
  }

  /**
   * Generate a deck.gl layer from this model description.
   */
  abstract render(): Layer;

  /**
   * Initialize a Table on the model.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  initTable(pythonName: string, jsName: string) {
    this[jsName] = parseParquetBuffers(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = parseParquetBuffers(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
  }

  async initLayerExtensions() {
    const childModelIds = this.model.get("_extensions");
    const childModels = await loadChildModels(
      this.model.widget_manager,
      childModelIds
    );

    const extensions: BaseExtensionModel[] = [];
    for (const childModel of childModels) {
      const extension = await initializeExtension(
        childModel,
        this.updateStateCallback
      );
      extensions.push(extension);
    }

    this.extensions = extensions;
  }
}

export class ScatterplotModel extends BaseLayerModel {
  static layerType = "scatterplot";

  protected radiusUnits: GeoArrowScatterplotLayerProps["radiusUnits"] | null;
  protected radiusScale: GeoArrowScatterplotLayerProps["radiusScale"] | null;
  protected radiusMinPixels:
    | GeoArrowScatterplotLayerProps["radiusMinPixels"]
    | null;
  protected radiusMaxPixels:
    | GeoArrowScatterplotLayerProps["radiusMaxPixels"]
    | null;
  protected lineWidthUnits:
    | GeoArrowScatterplotLayerProps["lineWidthUnits"]
    | null;
  protected lineWidthScale:
    | GeoArrowScatterplotLayerProps["lineWidthScale"]
    | null;
  protected lineWidthMinPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMinPixels"]
    | null;
  protected lineWidthMaxPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMaxPixels"]
    | null;
  protected stroked: GeoArrowScatterplotLayerProps["stroked"] | null;
  protected filled: GeoArrowScatterplotLayerProps["filled"] | null;
  protected billboard: GeoArrowScatterplotLayerProps["billboard"] | null;
  protected antialiasing: GeoArrowScatterplotLayerProps["antialiasing"] | null;
  protected getRadius: GeoArrowScatterplotLayerProps["getRadius"] | null;
  protected getFillColor: GeoArrowScatterplotLayerProps["getFillColor"] | null;
  protected getLineColor: GeoArrowScatterplotLayerProps["getLineColor"] | null;
  protected getLineWidth: GeoArrowScatterplotLayerProps["getLineWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("radius_units", "radiusUnits");
    this.initRegularAttribute("radius_scale", "radiusScale");
    this.initRegularAttribute("radius_min_pixels", "radiusMinPixels");
    this.initRegularAttribute("radius_max_pixels", "radiusMaxPixels");
    this.initRegularAttribute("line_width_units", "lineWidthUnits");
    this.initRegularAttribute("line_width_scale", "lineWidthScale");
    this.initRegularAttribute("line_width_min_pixels", "lineWidthMinPixels");
    this.initRegularAttribute("line_width_max_pixels", "lineWidthMaxPixels");
    this.initRegularAttribute("stroked", "stroked");
    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("billboard", "billboard");
    this.initRegularAttribute("antialiasing", "antialiasing");

    this.initVectorizedAccessor("get_radius", "getRadius");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
    this.initVectorizedAccessor("get_line_width", "getLineWidth");
  }

  render(): GeoArrowScatterplotLayer {
    return new GeoArrowScatterplotLayer({
      ...this.baseLayerProps(),
      // Note: this is included here instead of in baseLayerProps to satisfy
      // typing.
      data: this.table,

      ...(this.radiusUnits && { radiusUnits: this.radiusUnits }),
      ...(this.radiusScale && { radiusScale: this.radiusScale }),
      ...(this.radiusMinPixels && { radiusMinPixels: this.radiusMinPixels }),
      ...(this.radiusMaxPixels && { radiusMaxPixels: this.radiusMaxPixels }),
      ...(this.lineWidthUnits && { lineWidthUnits: this.lineWidthUnits }),
      ...(this.lineWidthScale && { lineWidthScale: this.lineWidthScale }),
      ...(this.lineWidthMinPixels && {
        lineWidthMinPixels: this.lineWidthMinPixels,
      }),
      ...(this.lineWidthMaxPixels && {
        lineWidthMaxPixels: this.lineWidthMaxPixels,
      }),
      ...(this.stroked && { stroked: this.stroked }),
      ...(this.filled && { filled: this.filled }),
      ...(this.billboard && { billboard: this.billboard }),
      ...(this.antialiasing && { antialiasing: this.antialiasing }),
      ...(this.getRadius && { getRadius: this.getRadius }),
      ...(this.getFillColor && { getFillColor: this.getFillColor }),
      ...(this.getLineColor && { getLineColor: this.getLineColor }),
      ...(this.getLineWidth && { getLineWidth: this.getLineWidth }),
    });
  }
}

export class PathModel extends BaseLayerModel {
  static layerType = "path";

  protected widthUnits: GeoArrowPathLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowPathLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowPathLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowPathLayerProps["widthMaxPixels"] | null;
  protected jointRounded: GeoArrowPathLayerProps["jointRounded"] | null;
  protected capRounded: GeoArrowPathLayerProps["capRounded"] | null;
  protected miterLimit: GeoArrowPathLayerProps["miterLimit"] | null;
  protected billboard: GeoArrowPathLayerProps["billboard"] | null;
  protected getColor: GeoArrowPathLayerProps["getColor"] | null;
  protected getWidth: GeoArrowPathLayerProps["getWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("width_units", "widthUnits");
    this.initRegularAttribute("width_scale", "widthScale");
    this.initRegularAttribute("width_min_pixels", "widthMinPixels");
    this.initRegularAttribute("width_max_pixels", "widthMaxPixels");
    this.initRegularAttribute("joint_rounded", "jointRounded");
    this.initRegularAttribute("cap_rounded", "capRounded");
    this.initRegularAttribute("miter_limit", "miterLimit");
    this.initRegularAttribute("billboard", "billboard");

    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_width", "getWidth");
  }

  render(): GeoArrowPathLayer {
    return new GeoArrowPathLayer({
      ...this.baseLayerProps(),
      // Note: this is included here instead of in baseLayerProps to satisfy
      // typing.
      data: this.table,

      ...(this.widthUnits && { widthUnits: this.widthUnits }),
      ...(this.widthScale && { widthScale: this.widthScale }),
      ...(this.widthMinPixels && { widthMinPixels: this.widthMinPixels }),
      ...(this.widthMaxPixels && { widthMaxPixels: this.widthMaxPixels }),
      ...(this.jointRounded && { jointRounded: this.jointRounded }),
      ...(this.capRounded && { capRounded: this.capRounded }),
      ...(this.miterLimit && { miterLimit: this.miterLimit }),
      ...(this.billboard && { billboard: this.billboard }),
      ...(this.getColor && { getColor: this.getColor }),
      ...(this.getWidth && { getWidth: this.getWidth }),
    });
  }
}

export class SolidPolygonModel extends BaseLayerModel {
  static layerType = "solid-polygon";

  protected filled: GeoArrowSolidPolygonLayerProps["filled"] | null;
  protected extruded: GeoArrowSolidPolygonLayerProps["extruded"] | null;
  protected wireframe: GeoArrowSolidPolygonLayerProps["wireframe"] | null;
  protected elevationScale:
    | GeoArrowSolidPolygonLayerProps["elevationScale"]
    | null;
  protected getElevation: GeoArrowSolidPolygonLayerProps["getElevation"] | null;
  protected getFillColor: GeoArrowSolidPolygonLayerProps["getFillColor"] | null;
  protected getLineColor: GeoArrowSolidPolygonLayerProps["getLineColor"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("extruded", "extruded");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("elevation_scale", "elevationScale");

    this.initVectorizedAccessor("get_elevation", "getElevation");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
  }

  render(): GeoArrowSolidPolygonLayer {
    return new GeoArrowSolidPolygonLayer({
      ...this.baseLayerProps(),
      // Note: this is included here instead of in baseLayerProps to satisfy
      // typing.
      data: this.table,

      ...(this.filled && { filled: this.filled }),
      ...(this.extruded && { extruded: this.extruded }),
      ...(this.wireframe && { wireframe: this.wireframe }),
      ...(this.elevationScale && { elevationScale: this.elevationScale }),
      ...(this.getElevation && { getElevation: this.getElevation }),
      ...(this.getFillColor && { getFillColor: this.getFillColor }),
      ...(this.getLineColor && { getLineColor: this.getLineColor }),
    });
  }
}

export async function initializeLayer(
  model: WidgetModel,
  updateStateCallback: () => void
): Promise<BaseLayerModel> {
  const layerType = model.get("_layer_type");
  switch (layerType) {
    case ScatterplotModel.layerType: {
      const layerModel = new ScatterplotModel(model, updateStateCallback);
      await layerModel.loadSubModels();
      return layerModel;
    }

    case PathModel.layerType: {
      const layerModel = new PathModel(model, updateStateCallback);
      await layerModel.loadSubModels();
      return layerModel;
    }

    case SolidPolygonModel.layerType: {
      const layerModel = new SolidPolygonModel(model, updateStateCallback);
      await layerModel.loadSubModels();
      return layerModel;
    }

    default:
      console.error(`no layer supported for ${layerType}`);
      break;
  }
}

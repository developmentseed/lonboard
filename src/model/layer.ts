import type { Layer, LayerExtension, LayerProps } from "@deck.gl/core/typed";
import {
  GeoArrowArcLayer,
  GeoArrowArcLayerProps,
  GeoArrowHeatmapLayer,
  GeoArrowHeatmapLayerProps,
  GeoArrowPathLayer,
  GeoArrowPathLayerProps,
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
  GeoArrowSolidPolygonLayer,
  GeoArrowSolidPolygonLayerProps,
} from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";
import { parseParquetBuffers } from "../parquet";
import { loadChildModels } from "../util";
import { BaseModel } from "./base";
import { BaseExtensionModel, initializeExtension } from "./extension";

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
    console.log("extensions", this.extensionInstances());
    console.log("extensionprops", this.extensionProps());
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

  // NOTE: this is flaky, especially when changing extensions
  // This is the main place where extensions should still be considered
  // experimental
  async initLayerExtensions() {
    const initExtensionsCallback = async () => {
      console.log("initExtensionsCallback");
      const childModelIds = this.model.get("extensions");
      if (!childModelIds) {
        this.extensions = [];
        return;
      }

      console.log(childModelIds);
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
    };
    await initExtensionsCallback();

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:extensions`);

    this.model.on(`change:extensions`, initExtensionsCallback);

    this.callbacks.set(`change:extensions`, initExtensionsCallback);
  }
}

export class ArcModel extends BaseLayerModel {
  static layerType = "arc";

  protected greatCircle: GeoArrowArcLayerProps["greatCircle"] | null;
  protected numSegments: GeoArrowArcLayerProps["numSegments"] | null;
  protected widthUnits: GeoArrowArcLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowArcLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowArcLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowArcLayerProps["widthMaxPixels"] | null;
  protected getSourcePosition:
    | GeoArrowArcLayerProps["getSourcePosition"]
    | null;
  protected getTargetPosition:
    | GeoArrowArcLayerProps["getTargetPosition"]
    | null;
  protected getSourceColor: GeoArrowArcLayerProps["getSourceColor"] | null;
  protected getTargetColor: GeoArrowArcLayerProps["getTargetColor"] | null;
  protected getWidth: GeoArrowArcLayerProps["getWidth"] | null;
  protected getHeight: GeoArrowArcLayerProps["getHeight"] | null;
  protected getTilt: GeoArrowArcLayerProps["getTilt"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("great_circle", "greatCircle");
    this.initRegularAttribute("num_segments", "numSegments");
    this.initRegularAttribute("width_units", "widthUnits");
    this.initRegularAttribute("width_scale", "widthScale");
    this.initRegularAttribute("width_min_pixels", "widthMinPixels");
    this.initRegularAttribute("width_max_pixels", "widthMaxPixels");

    this.initVectorizedAccessor("get_source_position", "getSourcePosition");
    this.initVectorizedAccessor("get_target_position", "getTargetPosition");
    this.initVectorizedAccessor("get_source_color", "getSourceColor");
    this.initVectorizedAccessor("get_target_color", "getTargetColor");
    this.initVectorizedAccessor("get_width", "getWidth");
    this.initVectorizedAccessor("get_height", "getHeight");
    this.initVectorizedAccessor("get_tilt", "getTilt");
  }

  render(): GeoArrowArcLayer {
    return new GeoArrowArcLayer({
      ...this.baseLayerProps(),
      // Note: this is included here instead of in baseLayerProps to satisfy
      // typing.
      data: this.table,

      ...(this.greatCircle && { greatCircle: this.greatCircle }),
      ...(this.numSegments && { numSegments: this.numSegments }),
      ...(this.widthUnits && { widthUnits: this.widthUnits }),
      ...(this.widthScale && { widthScale: this.widthScale }),
      ...(this.widthMinPixels && { widthMinPixels: this.widthMinPixels }),
      ...(this.widthMaxPixels && { widthMaxPixels: this.widthMaxPixels }),
      ...(this.getSourcePosition && {
        getSourcePosition: this.getSourcePosition,
      }),
      ...(this.getTargetPosition && {
        getTargetPosition: this.getTargetPosition,
      }),
      ...(this.getSourceColor && { getSourceColor: this.getSourceColor }),
      ...(this.getTargetColor && { getTargetColor: this.getTargetColor }),
      ...(this.getWidth && { getWidth: this.getWidth }),
      ...(this.getHeight && { getHeight: this.getHeight }),
      ...(this.getTilt && { getTilt: this.getTilt }),
    });
  }
}

export class HeatmapModel extends BaseLayerModel {
  static layerType = "heatmap";

  protected radiusPixels: GeoArrowHeatmapLayerProps["radiusPixels"] | null;
  protected colorRange: GeoArrowHeatmapLayerProps["colorRange"] | null;
  protected intensity: GeoArrowHeatmapLayerProps["intensity"] | null;
  protected threshold: GeoArrowHeatmapLayerProps["threshold"] | null;
  protected colorDomain: GeoArrowHeatmapLayerProps["colorDomain"] | null;
  protected aggregation: GeoArrowHeatmapLayerProps["aggregation"] | null;
  protected weightsTextureSize:
    | GeoArrowHeatmapLayerProps["weightsTextureSize"]
    | null;
  protected debounceTimeout:
    | GeoArrowHeatmapLayerProps["debounceTimeout"]
    | null;
  protected getPosition: GeoArrowHeatmapLayerProps["getPosition"] | null;
  protected getWeight: GeoArrowHeatmapLayerProps["getWeight"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("radius_pixels", "radiusPixels");
    this.initRegularAttribute("color_range", "colorRange");
    this.initRegularAttribute("intensity", "intensity");
    this.initRegularAttribute("threshold", "threshold");
    this.initRegularAttribute("color_domain", "colorDomain");
    this.initRegularAttribute("aggregation", "aggregation");
    this.initRegularAttribute("weights_texture_size", "weightsTextureSize");
    this.initRegularAttribute("debounce_timeout", "debounceTimeout");

    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_weight", "getWeight");
  }

  render(): GeoArrowHeatmapLayer {
    return new GeoArrowHeatmapLayer({
      ...this.baseLayerProps(),
      // Note: this is included here instead of in baseLayerProps to satisfy
      // typing.
      data: this.table,

      ...(this.radiusPixels && { radiusPixels: this.radiusPixels }),
      ...(this.colorRange && { colorRange: this.colorRange }),
      ...(this.intensity && { intensity: this.intensity }),
      ...(this.threshold && { threshold: this.threshold }),
      ...(this.colorDomain && { colorDomain: this.colorDomain }),
      ...(this.aggregation && { aggregation: this.aggregation }),
      ...(this.weightsTextureSize && {
        weightsTextureSize: this.weightsTextureSize,
      }),
      ...(this.debounceTimeout && { debounceTimeout: this.debounceTimeout }),
      ...(this.getPosition && { getPosition: this.getPosition }),
      ...(this.getWeight && { getWeight: this.getWeight }),
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
  let layerModel: BaseLayerModel;
  switch (layerType) {
    case ArcModel.layerType:
      layerModel = new ArcModel(model, updateStateCallback);
      break;

    case HeatmapModel.layerType:
      layerModel = new HeatmapModel(model, updateStateCallback);
      break;

    case PathModel.layerType:
      layerModel = new PathModel(model, updateStateCallback);
      break;

    case ScatterplotModel.layerType:
      layerModel = new ScatterplotModel(model, updateStateCallback);
      break;

    case SolidPolygonModel.layerType:
      layerModel = new SolidPolygonModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no layer supported for ${layerType}`);
  }

  await layerModel.loadSubModels();
  return layerModel;
}

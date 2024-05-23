import { LayerExtension } from "@deck.gl/core";
import {
  BrushingExtension as _BrushingExtension,
  CollisionFilterExtension as _CollisionFilterExtension,
  DataFilterExtension as _DataFilterExtension,
} from "@deck.gl/extensions";
import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./base.js";
import type { BaseLayerModel } from "./base-layer.js";
import { isDefined } from "../util.js";

export abstract class BaseExtensionModel extends BaseModel {
  static extensionType: string;

  abstract extensionInstance: LayerExtension;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
  }
}

export class BrushingExtension extends BaseExtensionModel {
  static extensionType = "brushing";

  extensionInstance: _BrushingExtension;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);
    this.extensionInstance = new _BrushingExtension();

    layerModel.initRegularAttribute("brushing_enabled", "brushingEnabled");
    layerModel.initRegularAttribute("brushing_target", "brushingTarget");
    layerModel.initRegularAttribute("brushing_radius", "brushingRadius");

    layerModel.initVectorizedAccessor(
      "get_brushing_target",
      "getBrushingTarget",
    );

    // Update the layer model with the list of the JS property names added by
    // this extension
    layerModel.extensionLayerPropertyNames = [
      ...layerModel.extensionLayerPropertyNames,
      "brushingEnabled",
      "brushingTarget",
      "brushingRadius",
      "getBrushingTarget",
    ];
  }
}

export class CollisionFilterExtension extends BaseExtensionModel {
  static extensionType = "collision-filter";

  extensionInstance: _CollisionFilterExtension;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);
    this.extensionInstance = new _CollisionFilterExtension();

    layerModel.initRegularAttribute("collision_enabled", "collisionEnabled");
    layerModel.initRegularAttribute("collision_group", "collisionGroup");
    layerModel.initRegularAttribute(
      "collision_test_props",
      "collisionTestProps",
    );

    layerModel.initVectorizedAccessor(
      "get_collision_priority",
      "getCollisionPriority",
    );

    // Update the layer model with the list of the JS property names added by
    // this extension
    layerModel.extensionLayerPropertyNames = [
      ...layerModel.extensionLayerPropertyNames,
      "collisionEnabled",
      "collisionGroup",
      "collisionTestProps",
      "getCollisionPriority",
    ];
  }
}

export class DataFilterExtension extends BaseExtensionModel {
  static extensionType = "data-filter";

  extensionInstance: _DataFilterExtension;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

    // TODO: set filterSize, fp64, countItems in constructor
    // TODO: should filter_size automatically update from python?
    const filterSize = this.model.get("filter_size");
    this.extensionInstance = new _DataFilterExtension({ filterSize });

    // Properties added by the extension onto the layer
    layerModel.initRegularAttribute("filter_enabled", "filterEnabled");
    layerModel.initRegularAttribute("filter_range", "filterRange");
    layerModel.initRegularAttribute("filter_soft_range", "filterSoftRange");
    layerModel.initRegularAttribute(
      "filter_transform_size",
      "filterTransformSize",
    );
    layerModel.initRegularAttribute(
      "filter_transform_color",
      "filterTransformColor",
    );

    layerModel.initVectorizedAccessor("get_filter_value", "getFilterValue");

    // Update the layer model with the list of the JS property names added by
    // this extension
    layerModel.extensionLayerPropertyNames = [
      ...layerModel.extensionLayerPropertyNames,
      "filterEnabled",
      "filterRange",
      "filterSoftRange",
      "filterTransformSize",
      "filterTransformColor",
      "getFilterValue",
    ];
  }
}

export class PathStyleExtension extends BaseExtensionModel {
  static extensionType = "path-style";

  extensionInstance: _PathStyleExtension;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

    const dash = this.model.get("dash");
    const highPrecisionDash = this.model.get("high_precision_dash");
    const offset = this.model.get("offset");
    this.extensionInstance = new _PathStyleExtension({
      ...(isDefined(dash) ? { dash } : {}),
      ...(isDefined(highPrecisionDash) ? { highPrecisionDash } : {}),
      ...(isDefined(offset) ? { offset } : {}),
    });

    // Properties added by the extension onto the layer
    layerModel.initRegularAttribute("dash_gap_pickable", "dashGapPickable");
    layerModel.initRegularAttribute("dash_justified", "dashJustified");
    layerModel.initVectorizedAccessor("get_dash_array", "getDashArray");
    layerModel.initVectorizedAccessor("get_offset", "getOffset");

    // Update the layer model with the list of the JS property names added by
    // this extension
    layerModel.extensionLayerPropertyNames = [
      ...layerModel.extensionLayerPropertyNames,
      "dashGapPickable",
      "dashJustified",
      "getDashArray",
      "getOffset",
    ];
  }
}

export async function initializeExtension(
  model: WidgetModel,
  layerModel: BaseLayerModel,
  updateStateCallback: () => void,
): Promise<BaseExtensionModel> {
  const extensionType = model.get("_extension_type");
  let extensionModel: BaseExtensionModel;
  switch (extensionType) {
    case BrushingExtension.extensionType:
      extensionModel = new BrushingExtension(
        model,
        layerModel,
        updateStateCallback,
      );
      break;

    case CollisionFilterExtension.extensionType:
      extensionModel = new CollisionFilterExtension(
        model,
        layerModel,
        updateStateCallback,
      );
      break;

    case DataFilterExtension.extensionType:
      extensionModel = new DataFilterExtension(
        model,
        layerModel,
        updateStateCallback,
      );
      break;

    case PathStyleExtension.extensionType:
      extensionModel = new PathStyleExtension(
        model,
        layerModel,
        updateStateCallback,
      );
      break;

    default:
      throw new Error(`no known model for extension type ${extensionType}`);
  }

  await extensionModel.loadSubModels();
  return extensionModel;
}

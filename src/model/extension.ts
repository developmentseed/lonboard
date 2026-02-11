import type { LayerExtension } from "@deck.gl/core";
import {
  BrushingExtension as _BrushingExtension,
  CollisionFilterExtension as _CollisionFilterExtension,
  DataFilterExtension as _DataFilterExtension,
  PathStyleExtension as _PathStyleExtension,
} from "@deck.gl/extensions";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined } from "../util.js";
import { BaseModel } from "./base.js";
import type { BaseLayerModel } from "./layer/base.js";

export abstract class BaseExtensionModel extends BaseModel {
  static extensionType: string;

  abstract extensionInstance(): LayerExtension | null;
}

export class BrushingExtension extends BaseExtensionModel {
  static extensionType = "brushing";

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

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

  extensionInstance(): _BrushingExtension {
    return new _BrushingExtension();
  }
}

export class CollisionFilterExtension extends BaseExtensionModel {
  static extensionType = "collision-filter";

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

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

  extensionInstance(): _CollisionFilterExtension {
    return new _CollisionFilterExtension();
  }
}

export class DataFilterExtension extends BaseExtensionModel {
  static extensionType = "data-filter";

  // DataFilterExtensionOptions is not exported
  protected categorySize?: 0 | 1 | 2 | 3 | 4;
  protected filterSize?: 0 | 1 | 2 | 3 | 4;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

    this.initRegularAttribute("filter_size", "filterSize");
    this.initRegularAttribute("category_size", "categorySize");

    // Properties added by the extension onto the layer
    layerModel.initRegularAttribute("filter_categories", "filterCategories");
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

    layerModel.initVectorizedAccessor(
      "get_filter_category",
      "getFilterCategory",
    );
    layerModel.initVectorizedAccessor("get_filter_value", "getFilterValue");

    // Update the layer model with the list of the JS property names added by
    // this extension
    layerModel.extensionLayerPropertyNames = [
      ...layerModel.extensionLayerPropertyNames,
      "filterCategories",
      "filterEnabled",
      "filterRange",
      "filterSoftRange",
      "filterTransformSize",
      "filterTransformColor",
      "getFilterCategory",
      "getFilterValue",
    ];
  }

  extensionInstance(): _DataFilterExtension | null {
    if (isDefined(this.filterSize) || isDefined(this.categorySize)) {
      const props = {
        ...(isDefined(this.filterSize)
          ? { filterSize: this.filterSize !== null ? this.filterSize : 0 }
          : {}),
        ...(isDefined(this.categorySize)
          ? { categorySize: this.categorySize !== null ? this.categorySize : 0 }
          : {}),
      };
      return new _DataFilterExtension(props);
    } else {
      return null;
    }
  }
}

export class PathStyleExtension extends BaseExtensionModel {
  static extensionType = "path-style";

  protected dash?: boolean;
  protected offset?: boolean;
  protected highPrecisionDash?: boolean;

  constructor(
    model: WidgetModel,
    layerModel: BaseLayerModel,
    updateStateCallback: () => void,
  ) {
    super(model, updateStateCallback);

    // PathStyleExtensionOptions is not exported
    this.initRegularAttribute("dash", "dash");
    this.initRegularAttribute("high_precision_dash", "highPrecisionDash");
    this.initRegularAttribute("offset", "offset");

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

  extensionInstance(): _PathStyleExtension {
    return new _PathStyleExtension({
      ...(isDefined(this.dash) ? { dash: this.dash } : {}),
      ...(isDefined(this.highPrecisionDash)
        ? { highPrecisionDash: this.highPrecisionDash }
        : {}),
      ...(isDefined(this.offset) ? { offset: this.offset } : {}),
    });
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

  return extensionModel;
}

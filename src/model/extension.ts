import { LayerExtension } from "@deck.gl/core/typed";
import {
  BrushingExtensionProps,
  CollisionFilterExtensionProps,
  DataFilterExtensionProps,
  BrushingExtension as _BrushingExtension,
  CollisionFilterExtension as _CollisionFilterExtension,
  DataFilterExtension as _DataFilterExtension,
} from "@deck.gl/extensions/typed";
import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./base.js";

export abstract class BaseExtensionModel extends BaseModel {
  static extensionType: string;

  abstract extensionInstance: LayerExtension;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
  }

  abstract extensionProps(): {};
}

export class BrushingExtension extends BaseExtensionModel {
  static extensionType = "brushing";

  extensionInstance: _BrushingExtension;

  protected getBrushingTarget?: BrushingExtensionProps["getBrushingTarget"];
  protected brushingEnabled?: BrushingExtensionProps["brushingEnabled"];
  protected brushingTarget?: BrushingExtensionProps["brushingTarget"];
  protected brushingRadius?: BrushingExtensionProps["brushingRadius"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
    this.extensionInstance = new _BrushingExtension();

    this.initRegularAttribute("brushing_enabled", "brushingEnabled");
    this.initRegularAttribute("brushing_target", "brushingTarget");
    this.initRegularAttribute("brushing_radius", "brushingRadius");

    this.initVectorizedAccessor("get_brushing_target", "getBrushingTarget");
  }

  extensionProps(): BrushingExtensionProps {
    // TODO: vectorized accessor array doesn't get set yet on data.attributes
    return {
      ...(this.getBrushingTarget && {
        getBrushingTarget: this.getBrushingTarget,
      }),
      ...(this.brushingEnabled && { brushingEnabled: this.brushingEnabled }),
      ...(this.brushingTarget && { brushingTarget: this.brushingTarget }),
      ...(this.brushingRadius && { brushingRadius: this.brushingRadius }),
    };
  }
}

export class CollisionFilterExtension extends BaseExtensionModel {
  static extensionType = "collision-filter";

  extensionInstance: _CollisionFilterExtension;

  protected collisionEnabled?: CollisionFilterExtensionProps["collisionEnabled"];
  protected collisionGroup?: CollisionFilterExtensionProps["collisionGroup"];
  protected collisionTestProps?: CollisionFilterExtensionProps["collisionTestProps"];
  protected getCollisionPriority?: CollisionFilterExtensionProps["getCollisionPriority"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
    this.extensionInstance = new _CollisionFilterExtension();

    this.initRegularAttribute("collision_enabled", "collisionEnabled");
    this.initRegularAttribute("collision_group", "collisionGroup");
    this.initRegularAttribute("collision_test_props", "collisionTestProps");

    this.initVectorizedAccessor(
      "get_collision_priority",
      "getCollisionPriority",
    );
  }

  extensionProps(): CollisionFilterExtensionProps {
    // @ts-expect-error
    return {
      ...(this.collisionEnabled !== undefined && { collisionEnabled: this.collisionEnabled }),
      ...(this.collisionGroup && { collisionGroup: this.collisionGroup }),
      ...(this.collisionTestProps && {
        collisionTestProps: this.collisionTestProps,
      }),
      ...(this.getCollisionPriority && {
        getCollisionPriority: this.getCollisionPriority,
      }),
    };
  }
}

export class DataFilterExtension extends BaseExtensionModel {
  static extensionType = "data-filter";

  extensionInstance: _DataFilterExtension;

  protected getFilterValue?: DataFilterExtensionProps["getFilterValue"];

  protected filterEnabled?: DataFilterExtensionProps["filterEnabled"];
  protected filterRange?: DataFilterExtensionProps["filterRange"];
  protected filterSoftRange?: DataFilterExtensionProps["filterSoftRange"];
  protected filterTransformSize?: DataFilterExtensionProps["filterTransformSize"];
  protected filterTransformColor?: DataFilterExtensionProps["filterTransformColor"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);
    // TODO: set filterSize, fp64, countItems in constructor
    this.extensionInstance = new _DataFilterExtension();

    this.initRegularAttribute("filter_enabled", "filterEnabled");
    this.initRegularAttribute("filter_range", "filterRange");
    this.initRegularAttribute("filter_soft_range", "filterSoftRange");
    this.initRegularAttribute("filter_transform_size", "filterTransformSize");
    this.initRegularAttribute("filter_transform_color", "filterTransformColor");

    this.initVectorizedAccessor("get_filter_value", "getFilterValue");
  }

  extensionProps(): DataFilterExtensionProps {
    return {
      ...(this.getFilterValue && { getFilterValue: this.getFilterValue }),
      ...(this.filterEnabled && { filterEnabled: this.filterEnabled }),
      ...(this.filterRange && { filterRange: this.filterRange }),
      ...(this.filterSoftRange && { filterSoftRange: this.filterSoftRange }),
      ...(this.filterTransformSize && {
        filterTransformSize: this.filterTransformSize,
      }),
      ...(this.filterTransformColor && {
        filterTransformColor: this.filterTransformColor,
      }),
    };
  }
}

export async function initializeExtension(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseExtensionModel> {
  const extensionType = model.get("_extension_type");
  let extensionModel: BaseExtensionModel;
  switch (extensionType) {
    case BrushingExtension.extensionType:
      extensionModel = new BrushingExtension(model, updateStateCallback);
      break;

    case CollisionFilterExtension.extensionType:
      extensionModel = new CollisionFilterExtension(model, updateStateCallback);
      break;

    case DataFilterExtension.extensionType:
      extensionModel = new DataFilterExtension(model, updateStateCallback);
      break;

    default:
      throw new Error(`no known model for extension type ${extensionType}`);
  }

  await extensionModel.loadSubModels();
  return extensionModel;
}

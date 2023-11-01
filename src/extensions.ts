import { LayerExtension } from "@deck.gl/core/typed";
import {
  BrushingExtensionProps,
  CollisionFilterExtensionProps,
  BrushingExtension as _BrushingExtension,
  CollisionFilterExtension as _CollisionFilterExtension,
} from "@deck.gl/extensions/typed";
import type { WidgetModel } from "@jupyter-widgets/base";
import { BaseModel } from "./model";

export abstract class BaseExtensionModel extends BaseModel {
  static extensionType: string;

  extensionInstance: LayerExtension;

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
      "getCollisionPriority"
    );
  }

  extensionProps(): CollisionFilterExtensionProps {
    // TODO: vectorized accessor array doesn't get set yet on data.attributes
    return {
      ...(this.collisionEnabled && { collisionEnabled: this.collisionEnabled }),
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

export async function initializeExtension(
  model: WidgetModel,
  updateStateCallback: () => void
): Promise<BaseExtensionModel> {
  const extensionType = model.get("_extension_type");
  switch (extensionType) {
    case BrushingExtension.extensionType: {
      const extension = new BrushingExtension(model, updateStateCallback);
      await extension.loadSubModels();
      return extension;
    }

    case CollisionFilterExtension.extensionType: {
      const extension = new CollisionFilterExtension(
        model,
        updateStateCallback
      );
      await extension.loadSubModels();
      return extension;
    }

    default:
      console.error(`no known model for ${extensionType}`);
      break;
  }
}

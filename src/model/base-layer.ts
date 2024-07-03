// NOTE: the content of this file is isolated to avoid circular imports.

import type {
  Layer,
  LayerExtension,
  LayerProps,
  PickingInfo,
} from "@deck.gl/core";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined, loadChildModels } from "../util.js";
import { initializeExtension } from "./extension.js";
import type { BaseExtensionModel } from "./extension.js";
import { BaseModel } from "./base.js";

export abstract class BaseLayerModel extends BaseModel {
  protected pickable: LayerProps["pickable"];
  protected visible: LayerProps["visible"];
  protected opacity: LayerProps["opacity"];
  protected autoHighlight: LayerProps["autoHighlight"];

  protected extensions: BaseExtensionModel[];

  /** Names of additional layer properties that are dynamically added by
   * extensions and should be rendered with layer attributes.
   */
  extensionLayerPropertyNames: string[] = [];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("pickable", "pickable");
    this.initRegularAttribute("visible", "visible");
    this.initRegularAttribute("opacity", "opacity");
    this.initRegularAttribute("auto_highlight", "autoHighlight");

    this.extensions = [];
  }

  async loadSubModels() {
    await this.initLayerExtensions();
  }

  extensionInstances(): LayerExtension[] {
    return this.extensions.map((extension) => extension.extensionInstance);
  }

  extensionProps() {
    let props: Record<string, any> = {};
    for (const layerPropertyName of this.extensionLayerPropertyNames) {
      if (isDefined(this[layerPropertyName as keyof this])) {
        props[layerPropertyName] = this[layerPropertyName as keyof this];
      }
    }
    return props;
  }

  onClick(pickingInfo: PickingInfo) {
    if (!pickingInfo.index) return;

    this.model.set("selected_index", pickingInfo.index);
    this.model.save_changes();
  }

  baseLayerProps(): LayerProps {
    // console.log("extensions", this.extensionInstances());
    // console.log("extensionprops", this.extensionProps());
    return {
      extensions: this.extensionInstances(),
      ...this.extensionProps(),
      id: this.model.model_id,
      pickable: this.pickable,
      visible: this.visible,
      opacity: this.opacity,
      autoHighlight: this.autoHighlight,
      onClick: this.onClick.bind(this),
    };
  }

  /**
   * Layer properties for this layer
   */
  abstract layerProps(): Omit<LayerProps, "id">;

  /**
   * Generate a deck.gl layer from this model description.
   */
  abstract render(): Layer;

  // NOTE: this is flaky, especially when changing extensions
  // This is the main place where extensions should still be considered
  // experimental
  async initLayerExtensions() {
    const initExtensionsCallback = async () => {
      const childModelIds = this.model.get("extensions");
      if (!childModelIds) {
        this.extensions = [];
        return;
      }

      const childModels = await loadChildModels(
        this.model.widget_manager,
        childModelIds,
      );

      const extensions: BaseExtensionModel[] = [];
      for (const childModel of childModels) {
        const extension = await initializeExtension(
          childModel,
          this,
          this.updateStateCallback,
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

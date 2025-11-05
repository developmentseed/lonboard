import type {
  Layer,
  LayerExtension,
  LayerProps,
  PickingInfo,
} from "@deck.gl/core";
import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";
import { Vector } from "apache-arrow";

import { parseParquetBuffers } from "../../parquet.js";
import { isDefined } from "../../util.js";
import { BaseModel } from "../base.js";
import { initializeExtension } from "../extension.js";
import type { BaseExtensionModel } from "../extension.js";
import { initializeChildModels } from "../initialize.js";

export abstract class BaseLayerModel extends BaseModel {
  protected pickable: LayerProps["pickable"];
  protected visible: LayerProps["visible"];
  protected opacity: LayerProps["opacity"];
  protected autoHighlight: LayerProps["autoHighlight"];
  protected highlightColor: LayerProps["highlightColor"];
  protected beforeId?: string;

  protected extensions: Record<string, BaseExtensionModel>;

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
    this.initRegularAttribute("highlight_color", "highlightColor");
    this.initRegularAttribute("before_id", "beforeId");
    this.initRegularAttribute("selected_bounds", "selectedBounds");

    this.extensions = {};
  }

  async loadSubModels() {
    await this.initLayerExtensions();
  }

  extensionInstances(): LayerExtension[] {
    return Object.values(this.extensions)
      .map((extension) => extension.extensionInstance())
      .filter((extensionInstance) => extensionInstance !== null);
  }

  extensionProps(batchIndex?: number): Record<string, unknown> {
    const props: Record<string, unknown> = {};
    for (const layerPropertyName of this.extensionLayerPropertyNames) {
      const value = this[layerPropertyName as keyof this];
      if (isDefined(value)) {
        if (value instanceof Vector) {
          props[layerPropertyName] = value.data[batchIndex ?? 0];
        } else {
          props[layerPropertyName] = value;
        }
      }
    }
    // console.log("extension props", props);
    return props;
  }

  onClick(pickingInfo: PickingInfo) {
    if (!pickingInfo.index) return;

    this.model.set("selected_index", pickingInfo.index);
    this.model.save_changes();
  }

  baseLayerProps(batchIndex?: number): Omit<LayerProps, "id"> {
    return {
      extensions: this.extensionInstances(),
      ...this.extensionProps(batchIndex),
      pickable: this.pickable,
      visible: this.visible,
      opacity: this.opacity,
      autoHighlight: this.autoHighlight,
      ...(isDefined(this.highlightColor) && {
        highlightColor: this.highlightColor,
      }),
      onClick: this.onClick.bind(this),
      ...(isDefined(this.beforeId) && {
        beforeId: this.beforeId,
      }),
    };
  }

  /**
   * Layer properties for this layer
   *
   * Arrow-based layers will pass in a `batchIndex` because a single layer model
   * will render multiple layers, one for each internal record batch of the
   * table.
   *
   * If the layer is not Arrow-based, `batchIndex` will be undefined.
   */
  abstract layerProps(batchIndex?: number): LayerProps;

  /**
   * Generate an array of deck.gl layers from this model description, one for
   * each internal record batch of the table.
   *
   * Most Arrow-based layers will implement this to return multiple layers.
   * Non-Arrow-based layers will typically return a single layer.
   */
  abstract render(): Layer | Layer[];

  // NOTE: this is flaky, especially when changing extensions
  // This is the main place where extensions should still be considered
  // experimental
  async initLayerExtensions() {
    const initExtensionsCallback = async () => {
      const extensionModelIds = this.model.get("extensions");

      const extensionModels = await initializeChildModels<BaseExtensionModel>(
        this.model.widget_manager,
        extensionModelIds,
        this.extensions,
        async (childModel: WidgetModel) =>
          initializeExtension(childModel, this, this.updateStateCallback),
      );

      this.extensions = extensionModels;
    };

    await initExtensionsCallback();

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:extensions`);

    this.model.on(`change:extensions`, initExtensionsCallback);

    this.callbacks.set(`change:extensions`, initExtensionsCallback);
  }
}

/**
 * An abstract base class for a layer that uses an Arrow Table as the data prop.
 */
export abstract class BaseArrowLayerModel extends BaseLayerModel {
  protected table!: arrow.Table;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table");
  }

  /**
   * Initialize a Table on the model.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   */
  initTable(pythonName: string) {
    this.table = parseParquetBuffers(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this.table = parseParquetBuffers(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
  }
}

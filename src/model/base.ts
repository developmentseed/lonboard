import { parseAccessor } from "../accessor.js";
import type {
  Layer,
  LayerExtension,
  LayerProps,
  PickingInfo,
} from "@deck.gl/core/typed";
import type { WidgetModel } from "@jupyter-widgets/base";
import { loadChildModels } from "../util.js";
import { BaseExtensionModel, initializeExtension } from "./extension.js";

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
  initRegularAttribute(pythonName: string, jsName: string) {
    this[jsName as keyof this] = this.model.get(pythonName);

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName as keyof this] = this.model.get(pythonName);
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
  initVectorizedAccessor(pythonName: string, jsName: string) {
    this[jsName as keyof this] = parseAccessor(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName as keyof this] = parseAccessor(this.model.get(pythonName));
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
      if (this[layerPropertyName as keyof this] !== undefined) {
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
      console.log("initExtensionsCallback");
      const childModelIds = this.model.get("extensions");
      if (!childModelIds) {
        this.extensions = [];
        return;
      }

      console.log(childModelIds);
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

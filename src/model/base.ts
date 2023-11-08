import type { WidgetModel } from "@jupyter-widgets/base";
import { parseAccessor } from "../accessor";


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

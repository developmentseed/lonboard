import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";

import { parseParquetBuffers } from "../../parquet.js";
import { BaseLayerModel } from "../base-layer.js";

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

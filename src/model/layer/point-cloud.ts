import { GeoArrowPointCloudLayer } from "@geoarrow/deck.gl-layers";
import type { GeoArrowPointCloudLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import { ColorAccessorInput, accessColorData, NormalVector } from "../types.js";
import { BaseArrowLayerModel } from "./arrow-base.js";

export class PointCloudModel extends BaseArrowLayerModel {
  static layerType = "point-cloud";

  protected sizeUnits: GeoArrowPointCloudLayerProps["sizeUnits"] | null;
  protected pointSize: GeoArrowPointCloudLayerProps["pointSize"] | null;
  // protected material: GeoArrowPointCloudLayerProps["material"] | null;

  protected getColor?: ColorAccessorInput | null;
  protected getNormal?: NormalVector | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("size_units", "sizeUnits");
    this.initRegularAttribute("point_size", "pointSize");

    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_normal", "getNormal");
  }

  layerProps(batchIndex: number): GeoArrowPointCloudLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      ...(isDefined(this.sizeUnits) && { sizeUnits: this.sizeUnits }),
      ...(isDefined(this.pointSize) && { pointSize: this.pointSize }),
      ...(isDefined(this.getColor) && {
        getColor: accessColorData(this.getColor, batchIndex),
      }),
      ...(isDefined(this.getNormal) && {
        getNormal: this.getNormal.data[batchIndex],
      }),
    };
  }

  render(): GeoArrowPointCloudLayer[] {
    const layers: GeoArrowPointCloudLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowPointCloudLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

import { GeoArrowPathLayer } from "@geoarrow/deck.gl-layers";
import type { GeoArrowPathLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import {
  ColorAccessorInput,
  FloatAccessorInput,
  accessColorData,
  accessFloatData,
} from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class PathModel extends BaseArrowLayerModel {
  static layerType = "path";

  protected widthUnits: GeoArrowPathLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowPathLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowPathLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowPathLayerProps["widthMaxPixels"] | null;
  protected jointRounded: GeoArrowPathLayerProps["jointRounded"] | null;
  protected capRounded: GeoArrowPathLayerProps["capRounded"] | null;
  protected miterLimit: GeoArrowPathLayerProps["miterLimit"] | null;
  protected billboard: GeoArrowPathLayerProps["billboard"] | null;

  protected getColor?: ColorAccessorInput | null;
  protected getWidth?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("width_units", "widthUnits");
    this.initRegularAttribute("width_scale", "widthScale");
    this.initRegularAttribute("width_min_pixels", "widthMinPixels");
    this.initRegularAttribute("width_max_pixels", "widthMaxPixels");
    this.initRegularAttribute("joint_rounded", "jointRounded");
    this.initRegularAttribute("cap_rounded", "capRounded");
    this.initRegularAttribute("miter_limit", "miterLimit");
    this.initRegularAttribute("billboard", "billboard");

    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_width", "getWidth");
  }

  layerProps(batchIndex: number): GeoArrowPathLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      ...(isDefined(this.widthUnits) && { widthUnits: this.widthUnits }),
      ...(isDefined(this.widthScale) && { widthScale: this.widthScale }),
      ...(isDefined(this.widthMinPixels) && {
        widthMinPixels: this.widthMinPixels,
      }),
      ...(isDefined(this.widthMaxPixels) && {
        widthMaxPixels: this.widthMaxPixels,
      }),
      ...(isDefined(this.jointRounded) && { jointRounded: this.jointRounded }),
      ...(isDefined(this.capRounded) && { capRounded: this.capRounded }),
      ...(isDefined(this.miterLimit) && { miterLimit: this.miterLimit }),
      ...(isDefined(this.billboard) && { billboard: this.billboard }),
      ...(isDefined(this.getColor) && {
        getColor: accessColorData(this.getColor, batchIndex),
      }),
      ...(isDefined(this.getWidth) && {
        getWidth: accessFloatData(this.getWidth, batchIndex),
      }),
    };
  }

  render(): GeoArrowPathLayer[] {
    const layers: GeoArrowPathLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowPathLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

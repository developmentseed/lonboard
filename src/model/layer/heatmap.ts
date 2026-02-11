import type { GeoArrowHeatmapLayerProps } from "@geoarrow/deck.gl-layers";
import { GeoArrowHeatmapLayer } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import type { FloatAccessorInput, PointVector } from "../types.js";
import { accessFloatData } from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class HeatmapModel extends BaseArrowLayerModel {
  static layerType = "heatmap";

  protected radiusPixels: GeoArrowHeatmapLayerProps["radiusPixels"] | null;
  protected colorRange: GeoArrowHeatmapLayerProps["colorRange"] | null;
  protected intensity: GeoArrowHeatmapLayerProps["intensity"] | null;
  protected threshold: GeoArrowHeatmapLayerProps["threshold"] | null;
  protected colorDomain: GeoArrowHeatmapLayerProps["colorDomain"] | null;
  protected aggregation: GeoArrowHeatmapLayerProps["aggregation"] | null;
  protected weightsTextureSize:
    | GeoArrowHeatmapLayerProps["weightsTextureSize"]
    | null;
  protected debounceTimeout:
    | GeoArrowHeatmapLayerProps["debounceTimeout"]
    | null;

  protected getPosition?: PointVector | null;
  protected getWeight?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("radius_pixels", "radiusPixels");
    this.initRegularAttribute("color_range", "colorRange");
    this.initRegularAttribute("intensity", "intensity");
    this.initRegularAttribute("threshold", "threshold");
    this.initRegularAttribute("color_domain", "colorDomain");
    this.initRegularAttribute("aggregation", "aggregation");
    this.initRegularAttribute("weights_texture_size", "weightsTextureSize");
    this.initRegularAttribute("debounce_timeout", "debounceTimeout");

    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_weight", "getWeight");
  }

  layerProps(batchIndex: number): GeoArrowHeatmapLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      ...(isDefined(this.radiusPixels) && { radiusPixels: this.radiusPixels }),
      ...(isDefined(this.colorRange) && { colorRange: this.colorRange }),
      ...(isDefined(this.intensity) && { intensity: this.intensity }),
      ...(isDefined(this.threshold) && { threshold: this.threshold }),
      ...(isDefined(this.colorDomain) && { colorDomain: this.colorDomain }),
      ...(isDefined(this.aggregation) && { aggregation: this.aggregation }),
      ...(isDefined(this.weightsTextureSize) && {
        weightsTextureSize: this.weightsTextureSize,
      }),
      ...(isDefined(this.debounceTimeout) && {
        debounceTimeout: this.debounceTimeout,
      }),
      ...(isDefined(this.getPosition) && {
        getPosition: this.getPosition.data[batchIndex],
      }),
      ...(isDefined(this.getWeight) && {
        getWeight: accessFloatData(this.getWeight, batchIndex),
      }),
    };
  }

  render(): GeoArrowHeatmapLayer[] {
    const layers: GeoArrowHeatmapLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowHeatmapLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

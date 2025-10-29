import { GeoArrowTripsLayer } from "@geoarrow/deck.gl-layers";
import type { GeoArrowTripsLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import {
  ColorAccessorInput,
  FloatAccessorInput,
  TimestampVector,
  accessColorData,
  accessFloatData,
} from "../types.js";
import { BaseArrowLayerModel } from "./arrow-base.js";

export class TripsModel extends BaseArrowLayerModel {
  static layerType = "trip";

  protected widthUnits: GeoArrowTripsLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowTripsLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowTripsLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowTripsLayerProps["widthMaxPixels"] | null;
  protected jointRounded: GeoArrowTripsLayerProps["jointRounded"] | null;
  protected capRounded: GeoArrowTripsLayerProps["capRounded"] | null;
  protected miterLimit: GeoArrowTripsLayerProps["miterLimit"] | null;
  protected billboard: GeoArrowTripsLayerProps["billboard"] | null;
  protected fadeTrail: GeoArrowTripsLayerProps["fadeTrail"] | null;
  protected trailLength: GeoArrowTripsLayerProps["trailLength"] | null;
  protected currentTime: GeoArrowTripsLayerProps["currentTime"] | null;

  protected getColor?: ColorAccessorInput | null;
  protected getWidth?: FloatAccessorInput | null;
  protected getTimestamps!: TimestampVector;

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
    this.initRegularAttribute("fade_trail", "fadeTrail");
    this.initRegularAttribute("trail_length", "trailLength");
    this.initRegularAttribute("_current_time", "currentTime");

    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_width", "getWidth");
    this.initVectorizedAccessor("get_timestamps", "getTimestamps");
  }

  layerProps(batchIndex: number): GeoArrowTripsLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      // Required argument
      getTimestamps: this.getTimestamps.data[batchIndex],
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
      ...(isDefined(this.fadeTrail) && { fadeTrail: this.fadeTrail }),
      ...(isDefined(this.trailLength) && { trailLength: this.trailLength }),
      ...(isDefined(this.currentTime) && { currentTime: this.currentTime }),
      ...(isDefined(this.getColor) && {
        getColor: accessColorData(this.getColor, batchIndex),
      }),
      ...(isDefined(this.getWidth) && {
        getWidth: accessFloatData(this.getWidth, batchIndex),
      }),
    };
  }

  render(): GeoArrowTripsLayer[] {
    const layers: GeoArrowTripsLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowTripsLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

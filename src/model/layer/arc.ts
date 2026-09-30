import type { GeoArrowArcLayerProps } from "@geoarrow/deck.gl-geoarrow";
import { GeoArrowArcLayer } from "@geoarrow/deck.gl-geoarrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import { omitUndefined } from "../../util.js";
import type {
  ColorAccessorInput,
  FloatAccessorInput,
  PointVector,
} from "../types.js";
import { accessColorData, accessFloatData } from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class ArcModel extends BaseArrowLayerModel {
  static layerType = "arc";

  protected greatCircle: GeoArrowArcLayerProps["greatCircle"] | null;
  protected numSegments: GeoArrowArcLayerProps["numSegments"] | null;
  protected widthUnits: GeoArrowArcLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowArcLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowArcLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowArcLayerProps["widthMaxPixels"] | null;

  protected getSourcePosition!: PointVector;
  protected getTargetPosition!: PointVector;
  protected getSourceColor?: ColorAccessorInput | null;
  protected getTargetColor?: ColorAccessorInput | null;
  protected getWidth?: FloatAccessorInput | null;
  protected getHeight?: FloatAccessorInput | null;
  protected getTilt?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("great_circle", "greatCircle");
    this.initRegularAttribute("num_segments", "numSegments");
    this.initRegularAttribute("width_units", "widthUnits");
    this.initRegularAttribute("width_scale", "widthScale");
    this.initRegularAttribute("width_min_pixels", "widthMinPixels");
    this.initRegularAttribute("width_max_pixels", "widthMaxPixels");

    this.initVectorizedAccessor("get_source_position", "getSourcePosition");
    this.initVectorizedAccessor("get_target_position", "getTargetPosition");
    this.initVectorizedAccessor("get_source_color", "getSourceColor");
    this.initVectorizedAccessor("get_target_color", "getTargetColor");
    this.initVectorizedAccessor("get_width", "getWidth");
    this.initVectorizedAccessor("get_height", "getHeight");
    this.initVectorizedAccessor("get_tilt", "getTilt");
  }

  layerProps(batchIndex: number): GeoArrowArcLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      // Always provided
      getSourcePosition: this.getSourcePosition.data[batchIndex],
      getTargetPosition: this.getTargetPosition.data[batchIndex],
      ...omitUndefined({
        greatCircle: this.greatCircle,
        numSegments: this.numSegments,
        widthUnits: this.widthUnits,
        widthScale: this.widthScale,
        widthMinPixels: this.widthMinPixels,
        widthMaxPixels: this.widthMaxPixels,
        getSourceColor: accessColorData(this.getSourceColor, batchIndex),
        getTargetColor: accessColorData(this.getTargetColor, batchIndex),
        getWidth: accessFloatData(this.getWidth, batchIndex),
        getHeight: accessFloatData(this.getHeight, batchIndex),
        getTilt: accessFloatData(this.getTilt, batchIndex),
      }),
    };
  }

  render(): GeoArrowArcLayer[] {
    const layers: GeoArrowArcLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowArcLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

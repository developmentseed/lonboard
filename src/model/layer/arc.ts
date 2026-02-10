import type { GeoArrowArcLayerProps } from "@geoarrow/deck.gl-layers";
import { GeoArrowArcLayer } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined } from "../../util.js";
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
      ...(isDefined(this.greatCircle) && { greatCircle: this.greatCircle }),
      ...(isDefined(this.numSegments) && { numSegments: this.numSegments }),
      ...(isDefined(this.widthUnits) && { widthUnits: this.widthUnits }),
      ...(isDefined(this.widthScale) && { widthScale: this.widthScale }),
      ...(isDefined(this.widthMinPixels) && {
        widthMinPixels: this.widthMinPixels,
      }),
      ...(isDefined(this.widthMaxPixels) && {
        widthMaxPixels: this.widthMaxPixels,
      }),
      ...(isDefined(this.getSourceColor) && {
        getSourceColor: accessColorData(this.getSourceColor, batchIndex),
      }),
      ...(isDefined(this.getTargetColor) && {
        getTargetColor: accessColorData(this.getTargetColor, batchIndex),
      }),
      ...(isDefined(this.getWidth) && {
        getWidth: accessFloatData(this.getWidth, batchIndex),
      }),
      ...(isDefined(this.getHeight) && {
        getHeight: accessFloatData(this.getHeight, batchIndex),
      }),
      ...(isDefined(this.getTilt) && {
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

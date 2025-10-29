import { GeoArrowScatterplotLayer } from "@geoarrow/deck.gl-layers";
import type { GeoArrowScatterplotLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import {
  ColorAccessorInput,
  FloatAccessorInput,
  accessColorData,
  accessFloatData,
} from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class ScatterplotModel extends BaseArrowLayerModel {
  static layerType = "scatterplot";

  protected radiusUnits: GeoArrowScatterplotLayerProps["radiusUnits"] | null;
  protected radiusScale: GeoArrowScatterplotLayerProps["radiusScale"] | null;
  protected radiusMinPixels:
    | GeoArrowScatterplotLayerProps["radiusMinPixels"]
    | null;
  protected radiusMaxPixels:
    | GeoArrowScatterplotLayerProps["radiusMaxPixels"]
    | null;
  protected lineWidthUnits:
    | GeoArrowScatterplotLayerProps["lineWidthUnits"]
    | null;
  protected lineWidthScale:
    | GeoArrowScatterplotLayerProps["lineWidthScale"]
    | null;
  protected lineWidthMinPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMinPixels"]
    | null;
  protected lineWidthMaxPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMaxPixels"]
    | null;
  protected stroked: GeoArrowScatterplotLayerProps["stroked"] | null;
  protected filled: GeoArrowScatterplotLayerProps["filled"] | null;
  protected billboard: GeoArrowScatterplotLayerProps["billboard"] | null;
  protected antialiasing: GeoArrowScatterplotLayerProps["antialiasing"] | null;

  protected getRadius?: FloatAccessorInput | null;
  protected getFillColor?: ColorAccessorInput | null;
  protected getLineColor?: ColorAccessorInput | null;
  protected getLineWidth?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("radius_units", "radiusUnits");
    this.initRegularAttribute("radius_scale", "radiusScale");
    this.initRegularAttribute("radius_min_pixels", "radiusMinPixels");
    this.initRegularAttribute("radius_max_pixels", "radiusMaxPixels");
    this.initRegularAttribute("line_width_units", "lineWidthUnits");
    this.initRegularAttribute("line_width_scale", "lineWidthScale");
    this.initRegularAttribute("line_width_min_pixels", "lineWidthMinPixels");
    this.initRegularAttribute("line_width_max_pixels", "lineWidthMaxPixels");
    this.initRegularAttribute("stroked", "stroked");
    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("billboard", "billboard");
    this.initRegularAttribute("antialiasing", "antialiasing");

    this.initVectorizedAccessor("get_radius", "getRadius");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
    this.initVectorizedAccessor("get_line_width", "getLineWidth");
  }

  layerProps(batchIndex: number): GeoArrowScatterplotLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      ...(isDefined(this.radiusUnits) && { radiusUnits: this.radiusUnits }),
      ...(isDefined(this.radiusScale) && { radiusScale: this.radiusScale }),
      ...(isDefined(this.radiusMinPixels) && {
        radiusMinPixels: this.radiusMinPixels,
      }),
      ...(isDefined(this.radiusMaxPixels) && {
        radiusMaxPixels: this.radiusMaxPixels,
      }),
      ...(isDefined(this.lineWidthUnits) && {
        lineWidthUnits: this.lineWidthUnits,
      }),
      ...(isDefined(this.lineWidthScale) && {
        lineWidthScale: this.lineWidthScale,
      }),
      ...(isDefined(this.lineWidthMinPixels) && {
        lineWidthMinPixels: this.lineWidthMinPixels,
      }),
      ...(isDefined(this.lineWidthMaxPixels) && {
        lineWidthMaxPixels: this.lineWidthMaxPixels,
      }),
      ...(isDefined(this.stroked) && { stroked: this.stroked }),
      ...(isDefined(this.filled) && { filled: this.filled }),
      ...(isDefined(this.billboard) && { billboard: this.billboard }),
      ...(isDefined(this.antialiasing) && { antialiasing: this.antialiasing }),
      ...(isDefined(this.getRadius) && {
        getRadius: accessFloatData(this.getRadius, batchIndex),
      }),
      ...(isDefined(this.getFillColor) && {
        getFillColor: accessColorData(this.getFillColor, batchIndex),
      }),
      ...(isDefined(this.getLineColor) && {
        getLineColor: accessColorData(this.getLineColor, batchIndex),
      }),
      ...(isDefined(this.getLineWidth) && {
        getLineWidth: accessFloatData(this.getLineWidth, batchIndex),
      }),
    };
  }

  render(): GeoArrowScatterplotLayer[] {
    const layers: GeoArrowScatterplotLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowScatterplotLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

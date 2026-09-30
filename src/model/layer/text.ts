import type { _GeoArrowTextLayerProps as GeoArrowTextLayerProps } from "@geoarrow/deck.gl-geoarrow";
import { _GeoArrowTextLayer as GeoArrowTextLayer } from "@geoarrow/deck.gl-geoarrow";
import type { WidgetModel } from "@jupyter-widgets/base";

import { omitUndefined } from "../../util.js";
import type {
  ColorAccessorInput,
  FloatAccessorInput,
  PixelOffsetAccessorInput,
  PointVector,
  StringAccessorInput,
  StringVector,
} from "../types.js";
import { accessColorData, accessFloatData } from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class TextModel extends BaseArrowLayerModel {
  static layerType = "text";

  protected billboard: GeoArrowTextLayerProps["billboard"] | null;
  protected sizeScale: GeoArrowTextLayerProps["sizeScale"] | null;
  protected sizeUnits: GeoArrowTextLayerProps["sizeUnits"] | null;
  protected sizeMinPixels: GeoArrowTextLayerProps["sizeMinPixels"] | null;
  protected sizeMaxPixels: GeoArrowTextLayerProps["sizeMaxPixels"] | null;
  // protected background: GeoArrowTextLayerProps["background"] | null;
  protected getBackgroundColor?: ColorAccessorInput | null;
  protected getBorderColor?: ColorAccessorInput | null;
  protected getBorderWidth?: FloatAccessorInput | null;

  protected backgroundPadding:
    | GeoArrowTextLayerProps["backgroundPadding"]
    | null;
  protected characterSet: GeoArrowTextLayerProps["characterSet"] | null;
  protected fontFamily: GeoArrowTextLayerProps["fontFamily"] | null;
  protected fontWeight: GeoArrowTextLayerProps["fontWeight"] | null;
  protected lineHeight: GeoArrowTextLayerProps["lineHeight"] | null;
  protected outlineWidth: GeoArrowTextLayerProps["outlineWidth"] | null;
  protected outlineColor: GeoArrowTextLayerProps["outlineColor"] | null;
  protected fontSettings: GeoArrowTextLayerProps["fontSettings"] | null;
  protected wordBreak: GeoArrowTextLayerProps["wordBreak"] | null;
  protected maxWidth: GeoArrowTextLayerProps["maxWidth"] | null;

  protected getText!: StringVector;
  protected getPosition?: PointVector | null;
  protected getColor?: ColorAccessorInput | null;
  protected getSize?: FloatAccessorInput | null;
  protected getAngle?: FloatAccessorInput | null;
  protected getTextAnchor?:
    | StringAccessorInput
    | "start"
    | "middle"
    | "end"
    | null;
  protected getAlignmentBaseline?:
    | StringAccessorInput
    | "top"
    | "center"
    | "bottom"
    | null;
  protected getPixelOffset?: PixelOffsetAccessorInput | [number, number] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("billboard", "billboard");
    this.initRegularAttribute("size_scale", "sizeScale");
    this.initRegularAttribute("size_units", "sizeUnits");
    this.initRegularAttribute("size_min_pixels", "sizeMinPixels");
    this.initRegularAttribute("size_max_pixels", "sizeMaxPixels");
    // this.initRegularAttribute("background", "background");
    this.initRegularAttribute("background_padding", "backgroundPadding");
    this.initRegularAttribute("character_set", "characterSet");
    this.initRegularAttribute("font_family", "fontFamily");
    this.initRegularAttribute("font_weight", "fontWeight");
    this.initRegularAttribute("line_height", "lineHeight");
    this.initRegularAttribute("outline_width", "outlineWidth");
    this.initRegularAttribute("outline_color", "outlineColor");
    this.initRegularAttribute("font_settings", "fontSettings");
    this.initRegularAttribute("word_break", "wordBreak");
    this.initRegularAttribute("max_width", "maxWidth");

    this.initVectorizedAccessor("get_background_color", "getBackgroundColor");
    this.initVectorizedAccessor("get_border_color", "getBorderColor");
    this.initVectorizedAccessor("get_border_width", "getBorderWidth");
    this.initVectorizedAccessor("get_text", "getText");
    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_size", "getSize");
    this.initVectorizedAccessor("get_angle", "getAngle");
    this.initVectorizedAccessor("get_text_anchor", "getTextAnchor");
    this.initVectorizedAccessor(
      "get_alignment_baseline",
      "getAlignmentBaseline",
    );
    this.initVectorizedAccessor("get_pixel_offset", "getPixelOffset");
  }

  layerProps(batchIndex: number): GeoArrowTextLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      // Always provided
      getText: this.getText.data[batchIndex],
      ...omitUndefined({
        billboard: this.billboard,
        sizeScale: this.sizeScale,
        sizeUnits: this.sizeUnits,
        sizeMinPixels: this.sizeMinPixels,
        sizeMaxPixels: this.sizeMaxPixels,
        // background: this.background,
        backgroundPadding: this.backgroundPadding,
        characterSet: this.characterSet,
        fontFamily: this.fontFamily,
        fontWeight: this.fontWeight,
        lineHeight: this.lineHeight,
        outlineWidth: this.outlineWidth,
        outlineColor: this.outlineColor,
        fontSettings: this.fontSettings,
        wordBreak: this.wordBreak,
        maxWidth: this.maxWidth,
        getBackgroundColor: accessColorData(
          this.getBackgroundColor,
          batchIndex,
        ),
        getBorderColor: accessColorData(this.getBorderColor, batchIndex),
        getBorderWidth: accessFloatData(this.getBorderWidth, batchIndex),
        getPosition: this.getPosition?.data[batchIndex],
        getColor: accessColorData(this.getColor, batchIndex),
        getSize: accessFloatData(this.getSize, batchIndex),
        getAngle: accessFloatData(this.getAngle, batchIndex),
        getTextAnchor:
          typeof this.getTextAnchor === "string"
            ? (this.getTextAnchor as "start" | "middle" | "end")
            : this.getTextAnchor?.data[batchIndex],
        getAlignmentBaseline:
          typeof this.getAlignmentBaseline === "string"
            ? (this.getAlignmentBaseline as "top" | "center" | "bottom")
            : this.getAlignmentBaseline?.data[batchIndex],
        getPixelOffset: Array.isArray(this.getPixelOffset)
          ? this.getPixelOffset
          : this.getPixelOffset?.data[batchIndex],
      }),
    };
  }

  render(): GeoArrowTextLayer[] {
    const layers: GeoArrowTextLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowTextLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

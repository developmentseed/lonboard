import { _GeoArrowTextLayer as GeoArrowTextLayer } from "@geoarrow/deck.gl-layers";
import type { _GeoArrowTextLayerProps as GeoArrowTextLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { isDefined } from "../../util.js";
import {
  PointVector,
  ColorAccessorInput,
  FloatAccessorInput,
  StringAccessorInput,
  PixelOffsetAccessorInput,
  accessColorData,
  accessFloatData,
  StringVector,
} from "../types.js";
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
      ...(isDefined(this.billboard) && { billboard: this.billboard }),
      ...(isDefined(this.sizeScale) && { sizeScale: this.sizeScale }),
      ...(isDefined(this.sizeUnits) && { sizeUnits: this.sizeUnits }),
      ...(isDefined(this.sizeMinPixels) && {
        sizeMinPixels: this.sizeMinPixels,
      }),
      ...(isDefined(this.sizeMaxPixels) && {
        sizeMaxPixels: this.sizeMaxPixels,
      }),
      // ...(isDefined(this.background) && {background: this.background}),
      ...(isDefined(this.backgroundPadding) && {
        backgroundPadding: this.backgroundPadding,
      }),
      ...(isDefined(this.characterSet) && { characterSet: this.characterSet }),
      ...(isDefined(this.fontFamily) && { fontFamily: this.fontFamily }),
      ...(isDefined(this.fontWeight) && { fontWeight: this.fontWeight }),
      ...(isDefined(this.lineHeight) && { lineHeight: this.lineHeight }),
      ...(isDefined(this.outlineWidth) && { outlineWidth: this.outlineWidth }),
      ...(isDefined(this.outlineColor) && { outlineColor: this.outlineColor }),
      ...(isDefined(this.fontSettings) && { fontSettings: this.fontSettings }),
      ...(isDefined(this.wordBreak) && { wordBreak: this.wordBreak }),
      ...(isDefined(this.maxWidth) && { maxWidth: this.maxWidth }),

      ...(isDefined(this.getBackgroundColor) && {
        getBackgroundColor: accessColorData(
          this.getBackgroundColor,
          batchIndex,
        ),
      }),
      ...(isDefined(this.getBorderColor) && {
        getBorderColor: accessColorData(this.getBorderColor, batchIndex),
      }),
      ...(isDefined(this.getBorderWidth) && {
        getBorderWidth: accessFloatData(this.getBorderWidth, batchIndex),
      }),
      ...(isDefined(this.getPosition) && {
        getPosition: this.getPosition.data[batchIndex],
      }),
      ...(isDefined(this.getColor) && {
        getColor: accessColorData(this.getColor, batchIndex),
      }),
      ...(isDefined(this.getSize) && {
        getSize: accessFloatData(this.getSize, batchIndex),
      }),
      ...(isDefined(this.getAngle) && {
        getAngle: accessFloatData(this.getAngle, batchIndex),
      }),
      ...(isDefined(this.getTextAnchor) && {
        getTextAnchor:
          typeof this.getTextAnchor === "string"
            ? (this.getTextAnchor as "start" | "middle" | "end")
            : this.getTextAnchor.data[batchIndex],
      }),
      ...(isDefined(this.getAlignmentBaseline) && {
        getAlignmentBaseline:
          typeof this.getAlignmentBaseline === "string"
            ? (this.getAlignmentBaseline as "top" | "center" | "bottom")
            : this.getAlignmentBaseline.data[batchIndex],
      }),
      ...(isDefined(this.getPixelOffset) && {
        getPixelOffset: Array.isArray(this.getPixelOffset)
          ? this.getPixelOffset
          : this.getPixelOffset.data[batchIndex],
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

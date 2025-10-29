import { GeoArrowColumnLayer } from "@geoarrow/deck.gl-layers";
import type { GeoArrowColumnLayerProps } from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";

import { BaseArrowLayerModel } from "./arrow-base.js";
import { isDefined } from "../../util.js";
import {
  PointVector,
  ColorAccessorInput,
  FloatAccessorInput,
  accessColorData,
  accessFloatData,
} from "../types.js";

export class ColumnModel extends BaseArrowLayerModel {
  static layerType = "column";

  protected diskResolution: GeoArrowColumnLayerProps["diskResolution"] | null;
  protected radius: GeoArrowColumnLayerProps["radius"] | null;
  protected angle: GeoArrowColumnLayerProps["angle"] | null;

  // Note: not yet exposed to Python
  // protected vertices: GeoArrowColumnLayerProps["vertices"] | null;
  protected offset: GeoArrowColumnLayerProps["offset"] | null;
  protected coverage: GeoArrowColumnLayerProps["coverage"] | null;
  protected elevationScale: GeoArrowColumnLayerProps["elevationScale"] | null;
  protected filled: GeoArrowColumnLayerProps["filled"] | null;
  protected stroked: GeoArrowColumnLayerProps["stroked"] | null;
  protected extruded: GeoArrowColumnLayerProps["extruded"] | null;
  protected wireframe: GeoArrowColumnLayerProps["wireframe"] | null;
  protected flatShading: GeoArrowColumnLayerProps["flatShading"] | null;
  protected radiusUnits: GeoArrowColumnLayerProps["radiusUnits"] | null;
  protected lineWidthUnits: GeoArrowColumnLayerProps["lineWidthUnits"] | null;
  protected lineWidthScale: GeoArrowColumnLayerProps["lineWidthScale"] | null;
  protected lineWidthMinPixels:
    | GeoArrowColumnLayerProps["lineWidthMinPixels"]
    | null;
  protected lineWidthMaxPixels:
    | GeoArrowColumnLayerProps["lineWidthMaxPixels"]
    | null;
  // Note: not yet exposed to Python
  // protected material: GeoArrowColumnLayerProps["material"] | null;

  protected getPosition?: PointVector | null;
  protected getFillColor?: ColorAccessorInput | null;
  protected getLineColor?: ColorAccessorInput | null;
  protected getElevation?: FloatAccessorInput | null;
  protected getLineWidth?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("disk_resolution", "diskResolution");
    this.initRegularAttribute("radius", "radius");
    this.initRegularAttribute("angle", "angle");
    // this.initRegularAttribute("vertices", "vertices");
    this.initRegularAttribute("offset", "offset");
    this.initRegularAttribute("coverage", "coverage");
    this.initRegularAttribute("elevation_scale", "elevationScale");
    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("stroked", "stroked");
    this.initRegularAttribute("extruded", "extruded");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("flat_shading", "flatShading");
    this.initRegularAttribute("radius_units", "radiusUnits");
    this.initRegularAttribute("line_width_units", "lineWidthUnits");
    this.initRegularAttribute("line_width_scale", "lineWidthScale");
    this.initRegularAttribute("line_width_min_pixels", "lineWidthMinPixels");
    this.initRegularAttribute("line_width_max_pixels", "lineWidthMaxPixels");
    // this.initRegularAttribute("material", "material");

    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
    this.initVectorizedAccessor("get_elevation", "getElevation");
    this.initVectorizedAccessor("get_line_width", "getLineWidth");
  }

  layerProps(batchIndex: number): GeoArrowColumnLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      ...(isDefined(this.diskResolution) && {
        diskResolution: this.diskResolution,
      }),
      ...(isDefined(this.radius) && { radius: this.radius }),
      ...(isDefined(this.angle) && { angle: this.angle }),
      // ...(isDefined(this.vertices) &&
      //   this.vertices !== undefined && { vertices: this.vertices }),
      ...(isDefined(this.offset) && { offset: this.offset }),
      ...(isDefined(this.coverage) && { coverage: this.coverage }),
      ...(isDefined(this.elevationScale) && {
        elevationScale: this.elevationScale,
      }),
      ...(isDefined(this.filled) && { filled: this.filled }),
      ...(isDefined(this.stroked) && { stroked: this.stroked }),
      ...(isDefined(this.extruded) && { extruded: this.extruded }),
      ...(isDefined(this.wireframe) && { wireframe: this.wireframe }),
      ...(isDefined(this.flatShading) && { flatShading: this.flatShading }),
      ...(isDefined(this.radiusUnits) && { radiusUnits: this.radiusUnits }),
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
      // ...(isDefined(this.material) && { material: this.material }),
      ...(isDefined(this.getPosition) && {
        getPosition: this.getPosition.data[batchIndex],
      }),
      ...(isDefined(this.getFillColor) && {
        getFillColor: accessColorData(this.getFillColor, batchIndex),
      }),
      ...(isDefined(this.getLineColor) && {
        getLineColor: accessColorData(this.getLineColor, batchIndex),
      }),
      ...(isDefined(this.getElevation) && {
        getElevation: accessFloatData(this.getElevation, batchIndex),
      }),
      ...(isDefined(this.getLineWidth) && {
        getLineWidth: accessFloatData(this.getLineWidth, batchIndex),
      }),
    };
  }

  render(): GeoArrowColumnLayer[] {
    const layers: GeoArrowColumnLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowColumnLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

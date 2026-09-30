import type { GeoArrowColumnLayerProps } from "@geoarrow/deck.gl-geoarrow";
import { GeoArrowColumnLayer } from "@geoarrow/deck.gl-geoarrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import { omitUndefined } from "../../util.js";
import type {
  ColorAccessorInput,
  FloatAccessorInput,
  PointVector,
} from "../types.js";
import { accessColorData, accessFloatData } from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

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
      ...omitUndefined({
        diskResolution: this.diskResolution,
        radius: this.radius,
        angle: this.angle,
        // vertices: this.vertices,
        offset: this.offset,
        coverage: this.coverage,
        elevationScale: this.elevationScale,
        filled: this.filled,
        stroked: this.stroked,
        extruded: this.extruded,
        wireframe: this.wireframe,
        flatShading: this.flatShading,
        radiusUnits: this.radiusUnits,
        lineWidthUnits: this.lineWidthUnits,
        lineWidthScale: this.lineWidthScale,
        lineWidthMinPixels: this.lineWidthMinPixels,
        lineWidthMaxPixels: this.lineWidthMaxPixels,
        // material: this.material,
        getPosition: this.getPosition?.data[batchIndex],
        getFillColor: accessColorData(this.getFillColor, batchIndex),
        getLineColor: accessColorData(this.getLineColor, batchIndex),
        getElevation: accessFloatData(this.getElevation, batchIndex),
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

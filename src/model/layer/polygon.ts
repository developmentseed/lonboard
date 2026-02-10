import type {
  GeoArrowA5LayerProps,
  GeoArrowGeohashLayerProps,
  GeoArrowH3HexagonLayerProps,
  GeoArrowPolygonLayerProps,
  GeoArrowS2LayerProps,
  GeoArrowSolidPolygonLayerProps,
} from "@geoarrow/deck.gl-layers";
import {
  GeoArrowA5Layer,
  GeoArrowGeohashLayer,
  GeoArrowH3HexagonLayer,
  GeoArrowPolygonLayer,
  GeoArrowS2Layer,
  GeoArrowSolidPolygonLayer,
} from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import type * as arrow from "apache-arrow";

import { isDefined } from "../../util.js";
import { EARCUT_WORKER_POOL } from "../earcut-pool.js";
import type { ColorAccessorInput, FloatAccessorInput } from "../types.js";
import { accessColorData, accessFloatData } from "../types.js";
import { BaseArrowLayerModel } from "./base.js";

export class SolidPolygonModel extends BaseArrowLayerModel {
  static layerType = "solid-polygon";

  protected filled: GeoArrowSolidPolygonLayerProps["filled"] | null;
  protected extruded: GeoArrowSolidPolygonLayerProps["extruded"] | null;
  protected wireframe: GeoArrowSolidPolygonLayerProps["wireframe"] | null;
  protected elevationScale:
    | GeoArrowSolidPolygonLayerProps["elevationScale"]
    | null;

  protected getElevation?: FloatAccessorInput | null;
  protected getFillColor?: ColorAccessorInput | null;
  protected getLineColor?: ColorAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("extruded", "extruded");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("elevation_scale", "elevationScale");

    this.initVectorizedAccessor("get_elevation", "getElevation");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
  }

  layerProps(batchIndex: number): GeoArrowSolidPolygonLayerProps {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      earcutWorkerPool: EARCUT_WORKER_POOL,
      ...(isDefined(this.filled) && { filled: this.filled }),
      ...(isDefined(this.extruded) && { extruded: this.extruded }),
      ...(isDefined(this.wireframe) && { wireframe: this.wireframe }),
      ...(isDefined(this.elevationScale) && {
        elevationScale: this.elevationScale,
      }),
      ...(isDefined(this.getElevation) && {
        getElevation: accessFloatData(this.getElevation, batchIndex),
      }),
      ...(isDefined(this.getFillColor) && {
        getFillColor: accessColorData(this.getFillColor, batchIndex),
      }),
      ...(isDefined(this.getLineColor) && {
        getLineColor: accessColorData(this.getLineColor, batchIndex),
      }),
    };
  }

  render(): GeoArrowSolidPolygonLayer[] {
    const layers: GeoArrowSolidPolygonLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowSolidPolygonLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

export abstract class BasePolygonModel extends BaseArrowLayerModel {
  protected stroked: GeoArrowPolygonLayerProps["stroked"] | null;
  protected filled: GeoArrowPolygonLayerProps["filled"] | null;
  protected extruded: GeoArrowPolygonLayerProps["extruded"] | null;
  protected wireframe: GeoArrowPolygonLayerProps["wireframe"] | null;
  protected elevationScale: GeoArrowPolygonLayerProps["elevationScale"] | null;
  protected lineWidthUnits: GeoArrowPolygonLayerProps["lineWidthUnits"] | null;
  protected lineWidthScale: GeoArrowPolygonLayerProps["lineWidthScale"] | null;
  protected lineWidthMinPixels:
    | GeoArrowPolygonLayerProps["lineWidthMinPixels"]
    | null;
  protected lineWidthMaxPixels:
    | GeoArrowPolygonLayerProps["lineWidthMaxPixels"]
    | null;
  protected lineJointRounded:
    | GeoArrowPolygonLayerProps["lineJointRounded"]
    | null;
  protected lineMiterLimit: GeoArrowPolygonLayerProps["lineMiterLimit"] | null;

  protected getFillColor?: ColorAccessorInput | null;
  protected getLineColor?: ColorAccessorInput | null;
  protected getLineWidth?: FloatAccessorInput | null;
  protected getElevation?: FloatAccessorInput | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("stroked", "stroked");
    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("extruded", "extruded");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("elevation_scale", "elevationScale");
    this.initRegularAttribute("line_width_units", "lineWidthUnits");
    this.initRegularAttribute("line_width_scale", "lineWidthScale");
    this.initRegularAttribute("line_width_min_pixels", "lineWidthMinPixels");
    this.initRegularAttribute("line_width_max_pixels", "lineWidthMaxPixels");
    this.initRegularAttribute("line_joint_rounded", "lineJointRounded");
    this.initRegularAttribute("line_miter_limit", "lineMiterLimit");

    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
    this.initVectorizedAccessor("get_line_width", "getLineWidth");
    this.initVectorizedAccessor("get_elevation", "getElevation");
  }

  basePolygonLayerProps(
    batchIndex: number,
  ): Omit<GeoArrowPolygonLayerProps, "getPolygon"> {
    return {
      id: `${this.model.model_id}-${batchIndex}`,
      data: this.table.batches[batchIndex],
      earcutWorkerPool: EARCUT_WORKER_POOL,
      ...(isDefined(this.stroked) && { stroked: this.stroked }),
      ...(isDefined(this.filled) && { filled: this.filled }),
      ...(isDefined(this.extruded) && { extruded: this.extruded }),
      ...(isDefined(this.wireframe) && { wireframe: this.wireframe }),
      ...(isDefined(this.elevationScale) && {
        elevationScale: this.elevationScale,
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
      ...(isDefined(this.lineJointRounded) && {
        lineJointRounded: this.lineJointRounded,
      }),
      ...(isDefined(this.lineMiterLimit) && {
        lineMiterLimit: this.lineMiterLimit,
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
      ...(isDefined(this.getElevation) && {
        getElevation: accessFloatData(this.getElevation, batchIndex),
      }),
    };
  }
}

export class PolygonModel extends BasePolygonModel {
  static layerType = "polygon";

  layerProps(batchIndex: number): GeoArrowPolygonLayerProps {
    return this.basePolygonLayerProps(batchIndex);
  }

  render(): GeoArrowPolygonLayer[] {
    const layers: GeoArrowPolygonLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowPolygonLayer({
          ...this.baseLayerProps(batchIdx),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

export class H3HexagonModel extends BasePolygonModel {
  static layerType = "h3-hexagon";

  protected highPrecision?: GeoArrowH3HexagonLayerProps["highPrecision"] | null;
  protected coverage?: GeoArrowH3HexagonLayerProps["coverage"] | null;

  protected getHexagon!: arrow.Vector<arrow.Uint64>;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("high_precision", "highPrecision");
    this.initRegularAttribute("coverage", "coverage");

    this.initVectorizedAccessor("get_hexagon", "getHexagon");
  }

  layerProps(batchIndex: number): GeoArrowH3HexagonLayerProps {
    return {
      getHexagon: this.getHexagon.data[batchIndex],
      ...(isDefined(this.highPrecision) && {
        highPrecision: this.highPrecision,
      }),
      ...(isDefined(this.coverage) && { coverage: this.coverage }),
      ...this.basePolygonLayerProps(batchIndex),
    };
  }

  render(): GeoArrowH3HexagonLayer[] {
    const layers: GeoArrowH3HexagonLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowH3HexagonLayer({
          ...this.baseLayerProps(),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

export class A5Model extends BasePolygonModel {
  static layerType = "a5";

  protected getPentagon!: arrow.Vector<arrow.Uint64>;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initVectorizedAccessor("get_pentagon", "getPentagon");
  }

  layerProps(batchIndex: number): GeoArrowA5LayerProps {
    return {
      getPentagon: this.getPentagon.data[batchIndex],
      ...this.basePolygonLayerProps(batchIndex),
    };
  }

  render(): GeoArrowA5Layer[] {
    const layers: GeoArrowA5Layer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowA5Layer({
          ...this.baseLayerProps(),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

export class GeohashModel extends BasePolygonModel {
  static layerType = "geohash";

  protected getGeohash!: arrow.Vector<arrow.Utf8>;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initVectorizedAccessor("get_geohash", "getGeohash");
  }

  layerProps(batchIndex: number): GeoArrowGeohashLayerProps {
    return {
      getGeohash: this.getGeohash.data[batchIndex],
      ...this.basePolygonLayerProps(batchIndex),
    };
  }

  render(): GeoArrowGeohashLayer[] {
    const layers: GeoArrowGeohashLayer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowGeohashLayer({
          ...this.baseLayerProps(),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

export class S2Model extends BasePolygonModel {
  static layerType = "s2";

  protected getS2Token!: arrow.Vector<arrow.Utf8>;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initVectorizedAccessor("get_s2_token", "getS2Token");
  }

  layerProps(batchIndex: number): GeoArrowS2LayerProps {
    return {
      getS2Token: this.getS2Token.data[batchIndex],
      ...this.basePolygonLayerProps(batchIndex),
    };
  }

  render(): GeoArrowS2Layer[] {
    const layers: GeoArrowS2Layer[] = [];
    for (let batchIdx = 0; batchIdx < this.table.batches.length; batchIdx++) {
      layers.push(
        new GeoArrowS2Layer({
          ...this.baseLayerProps(),
          ...this.layerProps(batchIdx),
        }),
      );
    }
    return layers;
  }
}

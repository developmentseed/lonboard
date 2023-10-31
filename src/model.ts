import {
  GeoArrowPathLayer,
  GeoArrowPathLayerProps,
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
  GeoArrowSolidPolygonLayer,
  GeoArrowSolidPolygonLayerProps,
} from "@geoarrow/deck.gl-layers";
import * as arrow from "apache-arrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import type { Layer } from "@deck.gl/core/typed";
import { parseParquetBuffers } from "./parquet";
import { parseAccessor } from "./accessor";

export abstract class BaseGeoArrowModel {
  model: WidgetModel;
  callbacks: Map<string, () => void>;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    this.model = model;
    this.model.on("change", updateStateCallback);
    this.callbacks = new Map();
  }

  /**
   * Generate a deck.gl layer from this model description.
   */
  abstract render(): Layer;

  /**
   * Finalize any resources held by the model
   */
  finalize(): void {
    for (const [pythonName, callback] of Object.entries(this.callbacks)) {
      this.model.off(`change:${pythonName}`, callback);
    }
  }

  /**
   * Initialize a Table on the model.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  initTable(pythonName: string, jsName: string) {
    this[jsName] = parseParquetBuffers(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = parseParquetBuffers(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(pythonName, callback);
  }

  /**
   * Initialize an attribute that does not need any transformation from its
   * serialized representation to its deck.gl representation.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  initRegularAttribute(pythonName: string, jsName: string) {
    this[jsName] = this.model.get(pythonName);

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = this.model.get(pythonName);
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(pythonName, callback);
  }

  /**
   * Initialize an accessor that can either be a scalar JSON value or a Parquet
   * table with a single column, intended to be passed in as an Arrow Vector.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   * @param   {string}  jsName      Name of attribute in deck.gl (usually camel-cased)
   */
  initVectorizedAccessor(pythonName: string, jsName: string) {
    this[jsName] = parseAccessor(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this[jsName] = parseAccessor(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(pythonName, callback);
  }
}

// TODO: should this extend WidgetModel? Maybe not to keep the import type-only?
export class ScatterplotModel extends BaseGeoArrowModel {
  table: arrow.Table;

  radiusUnits: GeoArrowScatterplotLayerProps["radiusUnits"] | null;
  radiusScale: GeoArrowScatterplotLayerProps["radiusScale"] | null;
  radiusMinPixels: GeoArrowScatterplotLayerProps["radiusMinPixels"] | null;
  radiusMaxPixels: GeoArrowScatterplotLayerProps["radiusMaxPixels"] | null;
  lineWidthUnits: GeoArrowScatterplotLayerProps["lineWidthUnits"] | null;
  lineWidthScale: GeoArrowScatterplotLayerProps["lineWidthScale"] | null;
  lineWidthMinPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMinPixels"]
    | null;
  lineWidthMaxPixels:
    | GeoArrowScatterplotLayerProps["lineWidthMaxPixels"]
    | null;
  stroked: GeoArrowScatterplotLayerProps["stroked"] | null;
  filled: GeoArrowScatterplotLayerProps["filled"] | null;
  billboard: GeoArrowScatterplotLayerProps["billboard"] | null;
  antialiasing: GeoArrowScatterplotLayerProps["antialiasing"] | null;
  getRadius: GeoArrowScatterplotLayerProps["getRadius"] | null;
  getFillColor: GeoArrowScatterplotLayerProps["getFillColor"] | null;
  getLineColor: GeoArrowScatterplotLayerProps["getLineColor"] | null;
  getLineWidth: GeoArrowScatterplotLayerProps["getLineWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table", "table");

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

  render(): GeoArrowScatterplotLayer {
    return new GeoArrowScatterplotLayer({
      id: this.model.model_id,
      data: this.table,
      ...(this.radiusUnits && { radiusUnits: this.radiusUnits }),
      ...(this.radiusScale && { radiusScale: this.radiusScale }),
      ...(this.radiusMinPixels && { radiusMinPixels: this.radiusMinPixels }),
      ...(this.radiusMaxPixels && { radiusMaxPixels: this.radiusMaxPixels }),
      ...(this.lineWidthUnits && { lineWidthUnits: this.lineWidthUnits }),
      ...(this.lineWidthScale && { lineWidthScale: this.lineWidthScale }),
      ...(this.lineWidthMinPixels && {
        lineWidthMinPixels: this.lineWidthMinPixels,
      }),
      ...(this.lineWidthMaxPixels && {
        lineWidthMaxPixels: this.lineWidthMaxPixels,
      }),
      ...(this.stroked && { stroked: this.stroked }),
      ...(this.filled && { filled: this.filled }),
      ...(this.billboard && { billboard: this.billboard }),
      ...(this.antialiasing && { antialiasing: this.antialiasing }),
      ...(this.getRadius && { getRadius: this.getRadius }),
      ...(this.getFillColor && { getFillColor: this.getFillColor }),
      ...(this.getLineColor && { getLineColor: this.getLineColor }),
      ...(this.getLineWidth && { getLineWidth: this.getLineWidth }),
      pickable: true,
    });
  }
}

export class PathModel extends BaseGeoArrowModel {
  table: arrow.Table;

  widthUnits: GeoArrowPathLayerProps["widthUnits"] | null;
  widthScale: GeoArrowPathLayerProps["widthScale"] | null;
  widthMinPixels: GeoArrowPathLayerProps["widthMinPixels"] | null;
  widthMaxPixels: GeoArrowPathLayerProps["widthMaxPixels"] | null;
  jointRounded: GeoArrowPathLayerProps["jointRounded"] | null;
  capRounded: GeoArrowPathLayerProps["capRounded"] | null;
  miterLimit: GeoArrowPathLayerProps["miterLimit"] | null;
  billboard: GeoArrowPathLayerProps["billboard"] | null;
  getColor: GeoArrowPathLayerProps["getColor"] | null;
  getWidth: GeoArrowPathLayerProps["getWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table", "table");

    this.initRegularAttribute("width_units", "widthUnits");
    this.initRegularAttribute("width_scale", "widthScale");
    this.initRegularAttribute("width_min_pixels", "widthMinPixels");
    this.initRegularAttribute("width_max_pixels", "widthMaxPixels");
    this.initRegularAttribute("joint_rounded", "jointRounded");
    this.initRegularAttribute("cap_rounded", "capRounded");
    this.initRegularAttribute("miter_limit", "miterLimit");
    this.initRegularAttribute("billboard", "billboard");

    this.initVectorizedAccessor("get_color", "getColor");
    this.initVectorizedAccessor("get_width", "getWidth");
  }

  render(): GeoArrowPathLayer {
    return new GeoArrowPathLayer({
      id: this.model.model_id,
      data: this.table,
      pickable: true,

      ...(this.widthUnits && { widthUnits: this.widthUnits }),
      ...(this.widthScale && { widthScale: this.widthScale }),
      ...(this.widthMinPixels && { widthMinPixels: this.widthMinPixels }),
      ...(this.widthMaxPixels && { widthMaxPixels: this.widthMaxPixels }),
      ...(this.jointRounded && { jointRounded: this.jointRounded }),
      ...(this.capRounded && { capRounded: this.capRounded }),
      ...(this.miterLimit && { miterLimit: this.miterLimit }),
      ...(this.billboard && { billboard: this.billboard }),
      ...(this.getColor && { getColor: this.getColor }),
      ...(this.getWidth && { getWidth: this.getWidth }),
    });
  }
}

export class SolidPolygonModel extends BaseGeoArrowModel {
  table: arrow.Table;

  filled: GeoArrowSolidPolygonLayerProps["filled"] | null;
  extruded: GeoArrowSolidPolygonLayerProps["extruded"] | null;
  wireframe: GeoArrowSolidPolygonLayerProps["wireframe"] | null;
  elevationScale: GeoArrowSolidPolygonLayerProps["elevationScale"] | null;
  getElevation: GeoArrowSolidPolygonLayerProps["getElevation"] | null;
  getFillColor: GeoArrowSolidPolygonLayerProps["getFillColor"] | null;
  getLineColor: GeoArrowSolidPolygonLayerProps["getLineColor"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table", "table");

    this.initRegularAttribute("filled", "filled");
    this.initRegularAttribute("extruded", "extruded");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("elevation_scale", "elevationScale");

    this.initVectorizedAccessor("get_elevation", "getElevation");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
  }

  render(): GeoArrowSolidPolygonLayer {
    return new GeoArrowSolidPolygonLayer({
      id: this.model.model_id,
      data: this.table,
      pickable: true,

      ...(this.filled && { filled: this.filled }),
      ...(this.extruded && { extruded: this.extruded }),
      ...(this.wireframe && { wireframe: this.wireframe }),
      ...(this.elevationScale && { elevationScale: this.elevationScale }),
      ...(this.getElevation && { getElevation: this.getElevation }),
      ...(this.getFillColor && { getFillColor: this.getFillColor }),
      ...(this.getLineColor && { getLineColor: this.getLineColor }),
    });
  }
}

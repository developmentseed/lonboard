import {
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
} from "@geoarrow/deck.gl-layers";
import * as arrow from "apache-arrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import { parseParquetBuffers } from "./parquet";
import { parseAccessor } from "./accessor";

class BaseGeoArrowModel {
  model: WidgetModel;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    this.model = model;
    this.model.on("change", updateStateCallback);
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
    this.model.on(`change:${pythonName}`, () => {
      console.log(`change:${pythonName}`);
      this[jsName] = parseParquetBuffers(this.model.get(pythonName));
    });
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
    this.model.on(`change:${pythonName}`, () => {
      this[jsName] = this.model.get(pythonName);
    });
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
    this.model.on(`change:${pythonName}`, () => {
      console.log(`change:${pythonName}`);
      this[jsName] = parseAccessor(this.model.get(pythonName));
      console.log(this[jsName]);
    });
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

import {
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
} from "@geoarrow/deck.gl-layers";
import * as arrow from "apache-arrow";
import type { WidgetModel } from "@jupyter-widgets/base";
import { parseParquetBuffers } from "./parquet";
import { parseAccessor } from "./accessor";

// TODO: should this extend WidgetModel? Maybe not to keep the import type-only?
export class ScatterplotModel {
  model: WidgetModel;

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
    this.model = model;

    this.table = parseParquetBuffers(model.get("table"));
    model.on("change:table", () => {
      console.log("change:table");
      this.table = parseParquetBuffers(this.model.get("table"));
    });

    this.radiusUnits = model.get("radius_units");
    model.on("change:radius_units", () => {
      console.log("change:radius_units");
      this.radiusUnits = model.get("radius_units");
    });

    model.
    this.radiusScale = model.get("radius_scale");
    model.on("change:radius_scale", () => {
      console.log("change:radius_scale");
      this.radiusScale = model.get("radius_scale");
    });

    // TODO: flesh out all attributes

    this.getFillColor = parseAccessor(model.get("get_fill_color"));
    model.on("change:get_fill_color", () => {
      console.log("change:get_fill_color");
      this.getFillColor = parseAccessor(this.model.get("get_fill_color"));
    });

    this.getLineColor = parseAccessor(model.get("get_line_color"));
    model.on("change:get_line_color", () => {
      console.log("change:get_line_color");
      this.getLineColor = parseAccessor(this.model.get("get_line_color"));
      console.log(this.getLineColor);
    });

    model.on("change", updateStateCallback);
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

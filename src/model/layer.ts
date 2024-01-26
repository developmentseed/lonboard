import {
  GeoArrowArcLayer,
  GeoArrowArcLayerProps,
  GeoArrowColumnLayer,
  GeoArrowColumnLayerProps,
  GeoArrowHeatmapLayer,
  GeoArrowHeatmapLayerProps,
  GeoArrowPathLayer,
  GeoArrowPathLayerProps,
  GeoArrowScatterplotLayer,
  GeoArrowScatterplotLayerProps,
  GeoArrowSolidPolygonLayer,
  GeoArrowSolidPolygonLayerProps,
  _GeoArrowTextLayer as GeoArrowTextLayer,
  _GeoArrowTextLayerProps as GeoArrowTextLayerProps,
} from "@geoarrow/deck.gl-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";
import { parseParquetBuffers } from "../parquet.js";
import { BaseLayerModel } from "./base-layer.js";
import { BitmapLayer, BitmapLayerProps } from "@deck.gl/layers/typed";
import { TileLayer, TileLayerProps } from "@deck.gl/geo-layers/typed";

/**
 * An abstract base class for a layer that uses an Arrow Table as the data prop.
 */
export abstract class BaseArrowLayerModel extends BaseLayerModel {
  protected table!: arrow.Table;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initTable("table");
  }

  /**
   * Initialize a Table on the model.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   */
  initTable(pythonName: string) {
    this.table = parseParquetBuffers(this.model.get(pythonName));

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    const callback = () => {
      this.table = parseParquetBuffers(this.model.get(pythonName));
    };
    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
  }
}

export class ArcModel extends BaseArrowLayerModel {
  static layerType = "arc";

  protected greatCircle: GeoArrowArcLayerProps["greatCircle"] | null;
  protected numSegments: GeoArrowArcLayerProps["numSegments"] | null;
  protected widthUnits: GeoArrowArcLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowArcLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowArcLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowArcLayerProps["widthMaxPixels"] | null;
  protected getSourcePosition!: GeoArrowArcLayerProps["getSourcePosition"];
  protected getTargetPosition!: GeoArrowArcLayerProps["getTargetPosition"];
  protected getSourceColor: GeoArrowArcLayerProps["getSourceColor"] | null;
  protected getTargetColor: GeoArrowArcLayerProps["getTargetColor"] | null;
  protected getWidth: GeoArrowArcLayerProps["getWidth"] | null;
  protected getHeight: GeoArrowArcLayerProps["getHeight"] | null;
  protected getTilt: GeoArrowArcLayerProps["getTilt"] | null;

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

  layerProps(): Omit<GeoArrowArcLayerProps, "id"> {
    return {
      data: this.table,
      // Always provided
      getSourcePosition: this.getSourcePosition,
      getTargetPosition: this.getTargetPosition,
      ...(this.greatCircle !== null && { greatCircle: this.greatCircle }),
      ...(this.numSegments !== null && { numSegments: this.numSegments }),
      ...(this.widthUnits !== null && { widthUnits: this.widthUnits }),
      ...(this.widthScale !== null && { widthScale: this.widthScale }),
      ...(this.widthMinPixels !== null && {
        widthMinPixels: this.widthMinPixels,
      }),
      ...(this.widthMaxPixels !== null && {
        widthMaxPixels: this.widthMaxPixels,
      }),
      ...(this.getSourceColor !== null && {
        getSourceColor: this.getSourceColor,
      }),
      ...(this.getTargetColor !== null && {
        getTargetColor: this.getTargetColor,
      }),
      ...(this.getWidth !== null && { getWidth: this.getWidth }),
      ...(this.getHeight !== null && { getHeight: this.getHeight }),
      ...(this.getTilt !== null && { getTilt: this.getTilt }),
    };
  }

  render(): GeoArrowArcLayer {
    return new GeoArrowArcLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class BitmapModel extends BaseLayerModel {
  static layerType = "bitmap";

  protected image: BitmapLayerProps["image"];
  protected bounds: BitmapLayerProps["bounds"];
  protected desaturate: BitmapLayerProps["desaturate"];
  protected transparentColor: BitmapLayerProps["transparentColor"];
  protected tintColor: BitmapLayerProps["tintColor"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("image", "image");
    this.initRegularAttribute("bounds", "bounds");
    this.initRegularAttribute("desaturate", "desaturate");
    this.initRegularAttribute("transparent_color", "transparentColor");
    this.initRegularAttribute("tint_color", "tintColor");
  }

  layerProps(): Omit<BitmapLayerProps, "id" | "data"> {
    return {
      ...(this.image !== null && { image: this.image }),
      ...(this.bounds !== null && { bounds: this.bounds }),
      ...(this.desaturate !== null && { desaturate: this.desaturate }),
      ...(this.transparentColor !== null && {
        transparentColor: this.transparentColor,
      }),
      ...(this.tintColor !== null && { tintColor: this.tintColor }),
    };
  }

  render(): BitmapLayer {
    return new BitmapLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      data: undefined,
      pickable: false,
    });
  }
}

export class BitmapTileModel extends BaseLayerModel {
  static layerType = "bitmap-tile";

  protected data!: TileLayerProps["data"];
  protected tileSize: TileLayerProps["tileSize"];
  protected zoomOffset: TileLayerProps["zoomOffset"];
  protected maxZoom: TileLayerProps["maxZoom"];
  protected minZoom: TileLayerProps["minZoom"];
  protected extent: TileLayerProps["extent"];
  protected maxCacheSize: TileLayerProps["maxCacheSize"];
  protected maxCacheByteSize: TileLayerProps["maxCacheByteSize"];
  protected refinementStrategy: TileLayerProps["refinementStrategy"];
  protected maxRequests: TileLayerProps["maxRequests"];

  protected desaturate: BitmapLayerProps["desaturate"];
  protected transparentColor: BitmapLayerProps["transparentColor"];
  protected tintColor: BitmapLayerProps["tintColor"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("data", "data");

    this.initRegularAttribute("tile_size", "tileSize");
    this.initRegularAttribute("zoom_offset", "zoomOffset");
    this.initRegularAttribute("max_zoom", "maxZoom");
    this.initRegularAttribute("min_zoom", "minZoom");
    this.initRegularAttribute("extent", "extent");
    this.initRegularAttribute("max_cache_size", "maxCacheSize");
    this.initRegularAttribute("max_cache_byte_size", "maxCacheByteSize");
    this.initRegularAttribute("refinement_strategy", "refinementStrategy");
    this.initRegularAttribute("max_requests", "maxRequests");
    this.initRegularAttribute("desaturate", "desaturate");
    this.initRegularAttribute("transparent_color", "transparentColor");
    this.initRegularAttribute("tint_color", "tintColor");
  }

  bitmapLayerProps(): Omit<BitmapLayerProps, "id" | "data"> {
    return {
      ...(this.desaturate !== null && { desaturate: this.desaturate }),
      ...(this.transparentColor !== null && {
        transparentColor: this.transparentColor,
      }),
      ...(this.tintColor !== null && { tintColor: this.tintColor }),
    };
  }

  layerProps(): Omit<TileLayerProps, "id"> {
    return {
      data: this.data,
      ...(this.tileSize !== null && { tileSize: this.tileSize }),
      ...(this.zoomOffset !== null && { zoomOffset: this.zoomOffset }),
      ...(this.maxZoom !== null && { maxZoom: this.maxZoom }),
      ...(this.minZoom !== null && { minZoom: this.minZoom }),
      ...(this.extent !== null && { extent: this.extent }),
      ...(this.maxCacheSize !== null && { maxCacheSize: this.maxCacheSize }),
      ...(this.maxCacheByteSize !== null && {
        maxCacheByteSize: this.maxCacheByteSize,
      }),
      ...(this.refinementStrategy !== null && {
        refinementStrategy: this.refinementStrategy,
      }),
      ...(this.maxRequests !== null && { maxRequests: this.maxRequests }),
    };
  }

  render(): TileLayer {
    return new TileLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),

      renderSubLayers: (props) => {
        const [min, max] = props.tile.boundingBox;

        return new BitmapLayer(props, {
          ...this.bitmapLayerProps(),
          data: undefined,
          image: props.data,
          bounds: [min[0], min[1], max[0], max[1]],
        });
      },
    });
  }
}

export class ColumnModel extends BaseArrowLayerModel {
  static layerType = "column";

  protected diskResolution: GeoArrowColumnLayerProps["diskResolution"] | null;
  protected radius: GeoArrowColumnLayerProps["radius"] | null;
  protected angle: GeoArrowColumnLayerProps["angle"] | null;

  // @ts-expect-error Property 'vertices' has no initializer and is not
  // definitely assigned in the constructor
  // Ref https://github.com/visgl/deck.gl/pull/8453
  protected vertices: GeoArrowColumnLayerProps["vertices"] | null;
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
  protected material: GeoArrowColumnLayerProps["material"] | null;
  protected getPosition: GeoArrowColumnLayerProps["getPosition"] | null;
  protected getFillColor: GeoArrowColumnLayerProps["getFillColor"] | null;
  protected getLineColor: GeoArrowColumnLayerProps["getLineColor"] | null;
  protected getElevation: GeoArrowColumnLayerProps["getElevation"] | null;
  protected getLineWidth: GeoArrowColumnLayerProps["getLineWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("disk_resolution", "diskResolution");
    this.initRegularAttribute("radius", "radius");
    this.initRegularAttribute("angle", "angle");
    this.initRegularAttribute("vertices", "vertices");
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
    this.initRegularAttribute("material", "material");

    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_fill_color", "getFillColor");
    this.initVectorizedAccessor("get_line_color", "getLineColor");
    this.initVectorizedAccessor("get_elevation", "getElevation");
    this.initVectorizedAccessor("get_line_width", "getLineWidth");
  }

  layerProps(): Omit<GeoArrowColumnLayerProps, "id"> {
    // @ts-expect-error Type 'Position[] | undefined' is not assignable to type
    // 'Position[] | null'.
    // Ref https://github.com/visgl/deck.gl/pull/8453
    return {
      data: this.table,
      ...(this.diskResolution !== null && {
        diskResolution: this.diskResolution,
      }),
      ...(this.radius !== null && { radius: this.radius }),
      ...(this.angle !== null && { angle: this.angle }),
      ...(this.vertices !== null &&
        this.vertices !== undefined && { vertices: this.vertices }),
      ...(this.offset !== null && { offset: this.offset }),
      ...(this.coverage !== null && { coverage: this.coverage }),
      ...(this.elevationScale !== null && {
        elevationScale: this.elevationScale,
      }),
      ...(this.filled !== null && { filled: this.filled }),
      ...(this.stroked !== null && { stroked: this.stroked }),
      ...(this.extruded !== null && { extruded: this.extruded }),
      ...(this.wireframe !== null && { wireframe: this.wireframe }),
      ...(this.flatShading !== null && { flatShading: this.flatShading }),
      ...(this.radiusUnits !== null && { radiusUnits: this.radiusUnits }),
      ...(this.lineWidthUnits !== null && {
        lineWidthUnits: this.lineWidthUnits,
      }),
      ...(this.lineWidthScale !== null && {
        lineWidthScale: this.lineWidthScale,
      }),
      ...(this.lineWidthMinPixels !== null && {
        lineWidthMinPixels: this.lineWidthMinPixels,
      }),
      ...(this.lineWidthMaxPixels !== null && {
        lineWidthMaxPixels: this.lineWidthMaxPixels,
      }),
      ...(this.material !== null && { material: this.material }),
      ...(this.getPosition !== null && { getPosition: this.getPosition }),
      ...(this.getFillColor !== null && { getFillColor: this.getFillColor }),
      ...(this.getLineColor !== null && { getLineColor: this.getLineColor }),
      ...(this.getElevation !== null && { getElevation: this.getElevation }),
      ...(this.getLineWidth !== null && { getLineWidth: this.getLineWidth }),
    };
  }

  render(): GeoArrowColumnLayer {
    return new GeoArrowColumnLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class HeatmapModel extends BaseArrowLayerModel {
  static layerType = "heatmap";

  protected radiusPixels: GeoArrowHeatmapLayerProps["radiusPixels"] | null;
  protected colorRange: GeoArrowHeatmapLayerProps["colorRange"] | null;
  protected intensity: GeoArrowHeatmapLayerProps["intensity"] | null;
  protected threshold: GeoArrowHeatmapLayerProps["threshold"] | null;
  protected colorDomain: GeoArrowHeatmapLayerProps["colorDomain"] | null;
  protected aggregation: GeoArrowHeatmapLayerProps["aggregation"] | null;
  protected weightsTextureSize:
    | GeoArrowHeatmapLayerProps["weightsTextureSize"]
    | null;
  protected debounceTimeout:
    | GeoArrowHeatmapLayerProps["debounceTimeout"]
    | null;
  protected getPosition: GeoArrowHeatmapLayerProps["getPosition"] | null;
  protected getWeight: GeoArrowHeatmapLayerProps["getWeight"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("radius_pixels", "radiusPixels");
    this.initRegularAttribute("color_range", "colorRange");
    this.initRegularAttribute("intensity", "intensity");
    this.initRegularAttribute("threshold", "threshold");
    this.initRegularAttribute("color_domain", "colorDomain");
    this.initRegularAttribute("aggregation", "aggregation");
    this.initRegularAttribute("weights_texture_size", "weightsTextureSize");
    this.initRegularAttribute("debounce_timeout", "debounceTimeout");

    this.initVectorizedAccessor("get_position", "getPosition");
    this.initVectorizedAccessor("get_weight", "getWeight");
  }

  layerProps(): Omit<GeoArrowHeatmapLayerProps, "id"> {
    return {
      data: this.table,
      ...(this.radiusPixels !== null && { radiusPixels: this.radiusPixels }),
      ...(this.colorRange !== null && { colorRange: this.colorRange }),
      ...(this.intensity !== null && { intensity: this.intensity }),
      ...(this.threshold !== null && { threshold: this.threshold }),
      ...(this.colorDomain !== null && { colorDomain: this.colorDomain }),
      ...(this.aggregation !== null && { aggregation: this.aggregation }),
      ...(this.weightsTextureSize !== null && {
        weightsTextureSize: this.weightsTextureSize,
      }),
      ...(this.debounceTimeout !== null && {
        debounceTimeout: this.debounceTimeout,
      }),
      ...(this.getPosition !== null && { getPosition: this.getPosition }),
      ...(this.getWeight !== null && { getWeight: this.getWeight }),
    };
  }

  render(): GeoArrowHeatmapLayer {
    return new GeoArrowHeatmapLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class PathModel extends BaseArrowLayerModel {
  static layerType = "path";

  protected widthUnits: GeoArrowPathLayerProps["widthUnits"] | null;
  protected widthScale: GeoArrowPathLayerProps["widthScale"] | null;
  protected widthMinPixels: GeoArrowPathLayerProps["widthMinPixels"] | null;
  protected widthMaxPixels: GeoArrowPathLayerProps["widthMaxPixels"] | null;
  protected jointRounded: GeoArrowPathLayerProps["jointRounded"] | null;
  protected capRounded: GeoArrowPathLayerProps["capRounded"] | null;
  protected miterLimit: GeoArrowPathLayerProps["miterLimit"] | null;
  protected billboard: GeoArrowPathLayerProps["billboard"] | null;
  protected getColor: GeoArrowPathLayerProps["getColor"] | null;
  protected getWidth: GeoArrowPathLayerProps["getWidth"] | null;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

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

  layerProps(): Omit<GeoArrowPathLayerProps, "id"> {
    return {
      data: this.table,
      ...(this.widthUnits !== null && { widthUnits: this.widthUnits }),
      ...(this.widthScale !== null && { widthScale: this.widthScale }),
      ...(this.widthMinPixels !== null && {
        widthMinPixels: this.widthMinPixels,
      }),
      ...(this.widthMaxPixels !== null && {
        widthMaxPixels: this.widthMaxPixels,
      }),
      ...(this.jointRounded !== null && { jointRounded: this.jointRounded }),
      ...(this.capRounded !== null && { capRounded: this.capRounded }),
      ...(this.miterLimit !== null && { miterLimit: this.miterLimit }),
      ...(this.billboard !== null && { billboard: this.billboard }),
      ...(this.getColor !== null && { getColor: this.getColor }),
      ...(this.getWidth !== null && { getWidth: this.getWidth }),
    };
  }

  render(): GeoArrowPathLayer {
    return new GeoArrowPathLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}
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
  protected getRadius: GeoArrowScatterplotLayerProps["getRadius"] | null;
  protected getFillColor: GeoArrowScatterplotLayerProps["getFillColor"] | null;
  protected getLineColor: GeoArrowScatterplotLayerProps["getLineColor"] | null;
  protected getLineWidth: GeoArrowScatterplotLayerProps["getLineWidth"] | null;

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

  layerProps(): Omit<GeoArrowScatterplotLayerProps, "id"> {
    console.log("stroked", this.stroked);

    return {
      data: this.table,
      ...(this.radiusUnits !== null && { radiusUnits: this.radiusUnits }),
      ...(this.radiusScale !== null && { radiusScale: this.radiusScale }),
      ...(this.radiusMinPixels !== null && {
        radiusMinPixels: this.radiusMinPixels,
      }),
      ...(this.radiusMaxPixels !== null && {
        radiusMaxPixels: this.radiusMaxPixels,
      }),
      ...(this.lineWidthUnits !== null && {
        lineWidthUnits: this.lineWidthUnits,
      }),
      ...(this.lineWidthScale !== null && {
        lineWidthScale: this.lineWidthScale,
      }),
      ...(this.lineWidthMinPixels !== null && {
        lineWidthMinPixels: this.lineWidthMinPixels,
      }),
      ...(this.lineWidthMaxPixels !== null && {
        lineWidthMaxPixels: this.lineWidthMaxPixels,
      }),
      ...(this.stroked !== null && { stroked: this.stroked }),
      ...(this.filled !== null && { filled: this.filled }),
      ...(this.billboard !== null && { billboard: this.billboard }),
      ...(this.antialiasing !== null && { antialiasing: this.antialiasing }),
      ...(this.getRadius !== null && { getRadius: this.getRadius }),
      ...(this.getFillColor !== null && { getFillColor: this.getFillColor }),
      ...(this.getLineColor !== null && { getLineColor: this.getLineColor }),
      ...(this.getLineWidth !== null && { getLineWidth: this.getLineWidth }),
    };
  }

  render(): GeoArrowScatterplotLayer {
    return new GeoArrowScatterplotLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class SolidPolygonModel extends BaseArrowLayerModel {
  static layerType = "solid-polygon";

  protected filled: GeoArrowSolidPolygonLayerProps["filled"] | null;
  protected extruded: GeoArrowSolidPolygonLayerProps["extruded"] | null;
  protected wireframe: GeoArrowSolidPolygonLayerProps["wireframe"] | null;
  protected elevationScale:
    | GeoArrowSolidPolygonLayerProps["elevationScale"]
    | null;
  protected getElevation: GeoArrowSolidPolygonLayerProps["getElevation"] | null;
  protected getFillColor: GeoArrowSolidPolygonLayerProps["getFillColor"] | null;
  protected getLineColor: GeoArrowSolidPolygonLayerProps["getLineColor"] | null;

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

  layerProps(): Omit<GeoArrowSolidPolygonLayerProps, "id"> {
    return {
      data: this.table,
      ...(this.filled !== null && { filled: this.filled }),
      ...(this.extruded !== null && { extruded: this.extruded }),
      ...(this.wireframe !== null && { wireframe: this.wireframe }),
      ...(this.elevationScale !== null && {
        elevationScale: this.elevationScale,
      }),
      ...(this.getElevation !== null && { getElevation: this.getElevation }),
      ...(this.getFillColor !== null && { getFillColor: this.getFillColor }),
      ...(this.getLineColor !== null && { getLineColor: this.getLineColor }),
    };
  }

  render(): GeoArrowSolidPolygonLayer {
    return new GeoArrowSolidPolygonLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class TextModel extends BaseArrowLayerModel {
  static layerType = "text";

  protected billboard: GeoArrowTextLayerProps["billboard"] | null;
  protected sizeScale: GeoArrowTextLayerProps["sizeScale"] | null;
  protected sizeUnits: GeoArrowTextLayerProps["sizeUnits"] | null;
  protected sizeMinPixels: GeoArrowTextLayerProps["sizeMinPixels"] | null;
  protected sizeMaxPixels: GeoArrowTextLayerProps["sizeMaxPixels"] | null;
  // protected background: GeoArrowTextLayerProps["background"] | null;
  protected getBackgroundColor:
    | GeoArrowTextLayerProps["getBackgroundColor"]
    | null;
  protected getBorderColor: GeoArrowTextLayerProps["getBorderColor"] | null;
  protected getBorderWidth: GeoArrowTextLayerProps["getBorderWidth"] | null;
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
  protected getText!: GeoArrowTextLayerProps["getText"];
  protected getPosition: GeoArrowTextLayerProps["getPosition"] | null;
  protected getColor: GeoArrowTextLayerProps["getColor"] | null;
  protected getSize: GeoArrowTextLayerProps["getSize"] | null;
  protected getAngle: GeoArrowTextLayerProps["getAngle"] | null;
  protected getTextAnchor: GeoArrowTextLayerProps["getTextAnchor"] | null;
  protected getAlignmentBaseline:
    | GeoArrowTextLayerProps["getAlignmentBaseline"]
    | null;
  protected getPixelOffset: GeoArrowTextLayerProps["getPixelOffset"] | null;

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

  layerProps(): Omit<GeoArrowTextLayerProps, "id"> {
    return {
      data: this.table,
      // Always provided
      getText: this.getText,
      ...(this.billboard !== null && { billboard: this.billboard }),
      ...(this.sizeScale !== null && { sizeScale: this.sizeScale }),
      ...(this.sizeUnits !== null && { sizeUnits: this.sizeUnits }),
      ...(this.sizeMinPixels !== null && { sizeMinPixels: this.sizeMinPixels }),
      ...(this.sizeMaxPixels !== null && { sizeMaxPixels: this.sizeMaxPixels }),
      // ...(this.background !== null && {background: this.background}),
      ...(this.backgroundPadding !== null && {
        backgroundPadding: this.backgroundPadding,
      }),
      ...(this.characterSet !== null && { characterSet: this.characterSet }),
      ...(this.fontFamily !== null && { fontFamily: this.fontFamily }),
      ...(this.fontWeight !== null && { fontWeight: this.fontWeight }),
      ...(this.lineHeight !== null && { lineHeight: this.lineHeight }),
      ...(this.outlineWidth !== null && { outlineWidth: this.outlineWidth }),
      ...(this.outlineColor !== null && { outlineColor: this.outlineColor }),
      ...(this.fontSettings !== null && { fontSettings: this.fontSettings }),
      ...(this.wordBreak !== null && { wordBreak: this.wordBreak }),
      ...(this.maxWidth !== null && { maxWidth: this.maxWidth }),

      ...(this.getBackgroundColor !== null && {
        getBackgroundColor: this.getBackgroundColor,
      }),
      ...(this.getBorderColor !== null && {
        getBorderColor: this.getBorderColor,
      }),
      ...(this.getBorderWidth !== null && {
        getBorderWidth: this.getBorderWidth,
      }),
      ...(this.getPosition !== null && { getPosition: this.getPosition }),
      ...(this.getColor !== null && { getColor: this.getColor }),
      ...(this.getSize !== null && { getSize: this.getSize }),
      ...(this.getAngle !== null && { getAngle: this.getAngle }),
      ...(this.getTextAnchor !== null && { getTextAnchor: this.getTextAnchor }),
      ...(this.getAlignmentBaseline !== null && {
        getAlignmentBaseline: this.getAlignmentBaseline,
      }),
      ...(this.getPixelOffset !== null && {
        getPixelOffset: this.getPixelOffset,
      }),
    };
  }

  render(): GeoArrowTextLayer {
    return new GeoArrowTextLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export async function initializeLayer(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseLayerModel> {
  const layerType = model.get("_layer_type");
  let layerModel: BaseLayerModel;
  switch (layerType) {
    case ArcModel.layerType:
      layerModel = new ArcModel(model, updateStateCallback);
      break;

    case BitmapModel.layerType:
      layerModel = new BitmapModel(model, updateStateCallback);
      break;

    case BitmapTileModel.layerType:
      layerModel = new BitmapTileModel(model, updateStateCallback);
      break;

    case ColumnModel.layerType:
      layerModel = new ColumnModel(model, updateStateCallback);
      break;

    case HeatmapModel.layerType:
      layerModel = new HeatmapModel(model, updateStateCallback);
      break;

    case PathModel.layerType:
      layerModel = new PathModel(model, updateStateCallback);
      break;

    case ScatterplotModel.layerType:
      layerModel = new ScatterplotModel(model, updateStateCallback);
      break;

    case SolidPolygonModel.layerType:
      layerModel = new SolidPolygonModel(model, updateStateCallback);
      break;

    case TextModel.layerType:
      layerModel = new TextModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no layer supported for ${layerType}`);
  }

  await layerModel.loadSubModels();
  return layerModel;
}

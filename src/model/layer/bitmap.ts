import type { TileLayerProps } from "@deck.gl/geo-layers";
import { TileLayer } from "@deck.gl/geo-layers";
import type { BitmapLayerProps } from "@deck.gl/layers";
import { BitmapLayer } from "@deck.gl/layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined } from "../../util.js";
import { BaseLayerModel } from "./base.js";

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

  layerProps(): Omit<BitmapLayerProps, "data"> {
    return {
      id: this.model.model_id,
      ...(isDefined(this.image) && { image: this.image }),
      ...(isDefined(this.bounds) && { bounds: this.bounds }),
      ...(isDefined(this.desaturate) && { desaturate: this.desaturate }),
      ...(isDefined(this.transparentColor) && {
        transparentColor: this.transparentColor,
      }),
      ...(isDefined(this.tintColor) && { tintColor: this.tintColor }),
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

  bitmapLayerProps(): Omit<BitmapLayerProps, "data"> {
    return {
      id: this.model.model_id,
      ...(isDefined(this.desaturate) && { desaturate: this.desaturate }),
      ...(isDefined(this.transparentColor) && {
        transparentColor: this.transparentColor,
      }),
      ...(isDefined(this.tintColor) && { tintColor: this.tintColor }),
    };
  }

  layerProps(): TileLayerProps {
    return {
      id: this.model.model_id,
      data: this.data,
      ...(isDefined(this.tileSize) && { tileSize: this.tileSize }),
      ...(isDefined(this.zoomOffset) && { zoomOffset: this.zoomOffset }),
      ...(isDefined(this.maxZoom) && { maxZoom: this.maxZoom }),
      ...(isDefined(this.minZoom) && { minZoom: this.minZoom }),
      ...(isDefined(this.extent) && { extent: this.extent }),
      ...(isDefined(this.maxCacheSize) && { maxCacheSize: this.maxCacheSize }),
      ...(isDefined(this.maxCacheByteSize) && {
        maxCacheByteSize: this.maxCacheByteSize,
      }),
      ...(isDefined(this.refinementStrategy) && {
        refinementStrategy: this.refinementStrategy,
      }),
      ...(isDefined(this.maxRequests) && { maxRequests: this.maxRequests }),
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

import type { TextureSource } from "@deck.gl/core";
import type {
  TileLayerProps,
  _Tileset2DProps as Tileset2DProps,
} from "@deck.gl/geo-layers";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { apply, invert } from "@developmentseed/affine";
import {
  RasterLayer,
  TileMatrixSetTileset,
} from "@developmentseed/deck.gl-raster";
import type { TileMatrixSet } from "@developmentseed/morecantile";
import { tileTransform } from "@developmentseed/morecantile";
import type { ReprojectionFns } from "@developmentseed/raster-reproject";
import type { WidgetModel } from "@jupyter-widgets/base";
import proj4 from "proj4";
import type { PROJJSONDefinition } from "proj4/dist/lib/core.js";
import { isDefined } from "../../util.js";
import { invoke } from "../dispatch.js";
import { BaseLayerModel } from "./base.js";

// This must be kept in sync with lonboard/layer/_raster.py
const MSG_KIND = "raster-get-tile-data";

type TileResponse =
  | { type: "empty" }
  | { type: "encoded-image"; media_type: string }
  | { error: string };

type TileData = {
  image: TextureSource;
  forwardTransform: ReprojectionFns["forwardTransform"];
  inverseTransform: ReprojectionFns["inverseTransform"];
};

export class RasterModel extends BaseLayerModel {
  static layerType = "raster";

  protected tileMatrixSet: TileMatrixSet | null | undefined;
  /** PROJJSON CRS */
  protected crs: PROJJSONDefinition | undefined;
  protected tileSize: TileLayerProps["tileSize"];
  protected zoomOffset: TileLayerProps["zoomOffset"];
  protected maxZoom: TileLayerProps["maxZoom"];
  protected minZoom: TileLayerProps["minZoom"];
  protected extent: TileLayerProps["extent"];
  protected maxCacheSize: TileLayerProps["maxCacheSize"];
  protected debounceTime: TileLayerProps["debounceTime"];

  /** proj4 converters from the source CRS to EPSG:4326 and EPSG:3857 */
  protected converters?: {
    4326: proj4.Converter;
    3857: proj4.Converter;
  };

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("_tile_matrix_set", "tileMatrixSet");
    this.initRegularAttribute("_crs", "crs");
    this.initRegularAttribute("_tile_size", "tileSize");
    this.initRegularAttribute("zoom_offset", "zoomOffset");
    this.initRegularAttribute("max_zoom", "maxZoom");
    this.initRegularAttribute("min_zoom", "minZoom");
    this.initRegularAttribute("extent", "extent");
    this.initRegularAttribute("max_cache_size", "maxCacheSize");
    this.initRegularAttribute("debounce_time", "debounceTime");

    if (this.crs) {
      this.converters = {
        4326: proj4(this.crs, "EPSG:4326"),
        3857: proj4(this.crs, "EPSG:3857"),
      };
    }

    // Note: if we change the name to public "crs" we'll have to change it here
    this.model.on("change:_crs", () => {
      const crs = this.model.get("_crs");
      this.converters = {
        4326: proj4(crs, "EPSG:4326"),
        3857: proj4(crs, "EPSG:3857"),
      };
    });
  }

  accessConverters() {
    const converters = this.converters;
    if (!converters) {
      throw new Error("CRS converters are not initialized");
    }

    return {
      forwardTo4326: (x: number, y: number): [number, number] =>
        converters[4326].forward([x, y]),
      inverseFrom4326: (x: number, y: number): [number, number] =>
        converters[4326].inverse([x, y]),
      forwardTo3857: (x: number, y: number): [number, number] =>
        converters[3857].forward([x, y]),
    };
  }

  layerProps(): TileLayerProps {
    return {
      id: `${this.model.model_id}`,
      data: null,
      ...(isDefined(this.tileSize) && { tileSize: this.tileSize }),
      ...(isDefined(this.zoomOffset) && { zoomOffset: this.zoomOffset }),
      ...(isDefined(this.maxZoom) && { maxZoom: this.maxZoom }),
      ...(isDefined(this.minZoom) && { minZoom: this.minZoom }),
      ...(isDefined(this.extent) && { extent: this.extent }),
      ...(isDefined(this.maxCacheSize) && { maxCacheSize: this.maxCacheSize }),
      ...(isDefined(this.debounceTime) && { debounceTime: this.debounceTime }),
    };
  }

  getTileData: TileLayerProps<TileData | null>["getTileData"] = async (
    tile,
  ) => {
    const { index } = tile;
    const { signal } = tile;
    const { x, y, z } = index;

    const [message, buffers] = await invoke<TileResponse>(
      this.model,
      {
        tile: {
          index: { x, y, z },
        },
      },
      MSG_KIND,
      { signal, timeout: 10000 },
    );

    // A tile intentionally out of bounds may return an "empty" message, which
    // is not an error.
    if ("type" in message && message.type === "empty") {
      return null;
    }

    if ("error" in message) {
      console.error("Error fetching tile data:", message.error);
      return null;
    }

    if (signal?.aborted) {
      return null;
    }

    const image = await dataViewToImageBitmap(buffers[0], message.media_type);

    // Compute per-tile affine transforms once; cached by TileLayer
    const tileMatrix = this.tileMatrixSet?.tileMatrices[z];
    if (!tileMatrix) {
      return null;
    }
    const tileAffine = tileTransform(tileMatrix, { col: x, row: y });
    const invAffine = invert(tileAffine);
    const forwardTransform = (u: number, v: number): [number, number] =>
      apply(tileAffine, u, v);
    const inverseTransform = (px: number, py: number): [number, number] =>
      apply(invAffine, px, py);

    return { image, forwardTransform, inverseTransform };
  };

  readonly renderRasterSubLayer: TileLayerProps<TileData | null>["renderSubLayers"] =
    (props) => {
      if (!props.data) {
        return null;
      }

      const { image, forwardTransform, inverseTransform } = props.data;
      const { inverseFrom4326, forwardTo4326 } = this.accessConverters();

      return new RasterLayer({
        id: `${props.id}-raster`,
        width: image.width,
        height: image.height,
        image,
        reprojectionFns: {
          forwardTransform,
          inverseTransform,
          forwardReproject: forwardTo4326,
          inverseReproject: inverseFrom4326,
        },
      });
    };

  renderTileMatrixSet(
    tileMatrixSet: TileMatrixSet,
    projectTo4326: (x: number, y: number) => [number, number],
    projectTo3857: (x: number, y: number) => [number, number],
  ): TileLayer {
    class TileMatrixSetTilesetFactory extends TileMatrixSetTileset {
      constructor(opts: Tileset2DProps) {
        super(opts, tileMatrixSet, {
          projectTo4326,
          projectTo3857,
        });
      }
    }

    return new TileLayer<TileData | null>({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      getTileData: this.getTileData,
      TilesetClass: TileMatrixSetTilesetFactory,
      renderSubLayers: this.renderRasterSubLayer,
    });
  }

  render(): TileLayer {
    const tileMatrixSet = this.tileMatrixSet;
    const converters = this.converters;
    if (tileMatrixSet && converters) {
      return this.renderTileMatrixSet(
        tileMatrixSet,
        (x, y) => converters[4326].forward([x, y]),
        (x, y) => converters[3857].forward([x, y]),
      );
    }

    return new TileLayer<TileData | null>({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      getTileData: this.getTileData,
      renderSubLayers: (props) => {
        const { tile } = props;
        const { boundingBox } = tile;

        if (!props.data || props.data === null) {
          return null;
        }

        const { image } = props.data;

        // @ts-expect-error props.data null not assignable to undefined
        return new BitmapLayer(props, {
          image,
          bounds: [
            boundingBox[0][0],
            boundingBox[0][1],
            boundingBox[1][0],
            boundingBox[1][1],
          ],
        });
      },
    });
  }
}

function dataViewToImageBitmap(
  dataView: DataView,
  mimeType: string,
): Promise<ImageBitmap> {
  const { buffer, byteOffset, byteLength } = dataView;

  if (!(buffer instanceof ArrayBuffer)) {
    throw new TypeError("SharedArrayBuffer is not supported");
  }

  const bytes = new Uint8Array(buffer, byteOffset, byteLength);
  const blob = new Blob([bytes], { type: mimeType });
  return createImageBitmap(blob);
}

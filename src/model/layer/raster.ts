import type {
  TileLayerProps,
  _Tileset2DProps as Tileset2DProps,
} from "@deck.gl/geo-layers";
import { TileLayer, _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { TileMatrixSetTileset } from "@developmentseed/deck.gl-raster";
import type { TileMatrixSet } from "@developmentseed/morecantile";
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
  | { type: "encoded-image"; mime_type: string }
  | { error: string };

export class RasterModel extends BaseLayerModel {
  static layerType = "raster";

  protected tms: TileMatrixSet | undefined;
  /** PROJJSON CRS */
  protected crs: PROJJSONDefinition | undefined;
  protected tileSize: TileLayerProps["tileSize"];
  protected zoomOffset: TileLayerProps["zoomOffset"];
  protected maxZoom: TileLayerProps["maxZoom"];
  protected minZoom: TileLayerProps["minZoom"];
  protected extent: TileLayerProps["extent"];
  protected maxCacheSize: TileLayerProps["maxCacheSize"];
  protected debounceTime: TileLayerProps["debounceTime"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("tms", "tms");
    this.initRegularAttribute("crs", "crs");
    this.initRegularAttribute("tile_size", "tileSize");
    this.initRegularAttribute("zoom_offset", "zoomOffset");
    this.initRegularAttribute("max_zoom", "maxZoom");
    this.initRegularAttribute("min_zoom", "minZoom");
    this.initRegularAttribute("extent", "extent");
    this.initRegularAttribute("max_cache_size", "maxCacheSize");
    this.initRegularAttribute("debounce_time", "debounceTime");
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

  getTileData: TileLayerProps["getTileData"] = async (tile) => {
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

    const image = await dataViewToImageBitmap(buffers[0], message.mime_type);

    return { message, buffers, image };
  };

  makeTileset2D(): TileLayerProps["TilesetClass"] {
    const tms = this.tms;
    const crs = this.crs;
    if (!tms || !crs) {
      return Tileset2D;
    }

    const forwardTo4326 = proj4(crs, "EPSG:4326").forward;
    const forwardTo3857 = proj4(crs, "EPSG:3857").forward;

    class TileMatrixSetTilesetFactory extends TileMatrixSetTileset {
      constructor(opts: Tileset2DProps) {
        super(opts, tms, {
          projectTo4326: forwardTo4326,
          projectTo3857: forwardTo3857,
        });
      }
    }

    return TileMatrixSetTilesetFactory;
  }

  render(): TileLayer {
    const TilesetClass = this.makeTileset2D();

    return new TileLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      getTileData: this.getTileData?.bind(this),
      TilesetClass,
      renderSubLayers: (props) => {
        const { tile } = props;
        const { boundingBox } = tile;

        if (!props.data) {
          return null;
        }

        console.log("props.data");
        console.log(props.data);
        const { image } = props.data;
        console.log("in renderSubLayers");
        console.log(props);

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

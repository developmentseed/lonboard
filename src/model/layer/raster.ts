import type { TileLayerProps } from "@deck.gl/geo-layers";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import { isDefined } from "../../util.js";
import { invoke } from "../dispatch.js";
import { BaseLayerModel } from "./base.js";

// This must be kept in sync with lonboard/layer/_raster.py
const MSG_KIND = "raster-get-tile-data";

export class RasterModel extends BaseLayerModel {
  static layerType = "raster";

  protected tileSize: TileLayerProps["tileSize"];
  protected zoomOffset: TileLayerProps["zoomOffset"];
  protected maxZoom: TileLayerProps["maxZoom"];
  protected minZoom: TileLayerProps["minZoom"];
  protected extent: TileLayerProps["extent"];
  protected maxCacheSize: TileLayerProps["maxCacheSize"];
  protected debounceTime: TileLayerProps["debounceTime"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("tile_size", "tileSize");
    this.initRegularAttribute("zoom_offset", "zoomOffset");
    this.initRegularAttribute("max_zoom", "maxZoom");
    this.initRegularAttribute("min_zoom", "minZoom");
    this.initRegularAttribute("extent", "extent");
    this.initRegularAttribute("max_cache_size", "maxCacheSize");
    this.initRegularAttribute("debounce_time", "debounceTime");
  }

  getTileData: TileLayerProps["getTileData"] = async (tile) => {
    const { index } = tile;
    const { signal } = tile;
    const { x, y, z } = index;
    console.log("in getTileData");

    console.log("calling invoke");
    console.log(tile);
    const [message, buffers] = await invoke(
      this.model,
      {
        tile: {
          index: { x, y, z },
        },
      },
      MSG_KIND,
      { signal, timeout: 10000 },
    );

    console.log(
      "returned from invoke, message and buffer received",
      message,
      buffers,
    );

    if (signal?.aborted) {
      return null;
    }

    const image = await dataViewToImageBitmap(buffers[0]);

    console.log("returned from invoke");
    console.log(message);

    return { message, buffers, image };
  };

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

  render(): TileLayer {
    return new TileLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      getTileData: this.getTileData?.bind(this),
      renderSubLayers: (props) => {
        const { tile } = props;
        const { boundingBox } = tile;
        const { image } = props.data;
        console.log("in renderSubLayers");
        console.log(props);

        return new BitmapLayer(props, {
          data: null,
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

async function dataViewToImageBitmap(dataView: DataView): Promise<ImageBitmap> {
  const { buffer, byteOffset, byteLength } = dataView;

  if (!(buffer instanceof ArrayBuffer)) {
    throw new TypeError("SharedArrayBuffer is not supported");
  }

  const bytes = new Uint8Array(buffer, byteOffset, byteLength);
  const blob = new Blob([bytes], { type: "image/png" });
  return createImageBitmap(blob);
}

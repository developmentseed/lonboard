import type { TileLayerProps } from "@deck.gl/geo-layers";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import { invoke } from "../dispatch.js";
import { BaseLayerModel } from "./base.js";

// This must be kept in sync with lonboard/layer/_raster.py
const MSG_KIND = "raster-get-tile-data";

export class RasterModel extends BaseLayerModel {
  static layerType = "raster";

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

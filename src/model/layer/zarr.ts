// SPIKE, not for merge: a layer whose data crosses the comm as zarr chunks and
// is styled on the GPU.
import type { MinimalTileData } from "@developmentseed/deck.gl-raster";
import {
  CreateTexture,
  LinearRescale,
} from "@developmentseed/deck.gl-raster/gpu-modules";
import type { GetTileDataOptions } from "@developmentseed/deck.gl-zarr";
import { ZarrLayer } from "@developmentseed/deck.gl-zarr";
import type { WidgetModel } from "@jupyter-widgets/base";
import type { Texture } from "@luma.gl/core";
import memoizeOne from "memoize-one";
import * as zarr from "zarrita";
import { invoke } from "../dispatch.js";
import { BaseLayerModel } from "./base.js";

// This must be kept in sync with lonboard/layer/_zarr.py
const MSG_KIND = "zarr-get";

type GetResponse = { type: "bytes" } | { type: "missing" } | { error: string };

type TileData = MinimalTileData & { texture: Texture };

/** A zarrita store whose chunk reads are answered by Python over the comm. */
export class CommStore implements zarr.AsyncReadable {
  constructor(
    private model: WidgetModel,
    /** `zarr.json` documents by key, sent up front as layer state. */
    private metadata: Record<string, unknown>,
  ) {}

  async get(
    key: zarr.AbsolutePath,
    opts?: { signal?: AbortSignal },
  ): Promise<Uint8Array | undefined> {
    if (key in this.metadata) {
      return new TextEncoder().encode(JSON.stringify(this.metadata[key]));
    }
    // Only chunk keys go to Python. Any other key is a metadata document the
    // layer state doesn't have, so it doesn't exist.
    if (!key.includes("/c/")) {
      return undefined;
    }

    const [message, buffers] = await invoke<GetResponse>(
      this.model,
      { key },
      MSG_KIND,
      { signal: opts?.signal },
    );
    if ("error" in message) {
      throw new Error(message.error);
    }
    if (message.type === "missing") {
      return undefined;
    }
    const { buffer, byteOffset, byteLength } = buffers[0];
    return new Uint8Array(buffer as ArrayBuffer, byteOffset, byteLength);
  }
}

export class ZarrModel extends BaseLayerModel {
  static layerType = "zarr";

  protected metadata: Record<string, unknown> | undefined;
  protected selection: Record<string, number> | undefined;
  protected rescaleMin: number | undefined;
  protected rescaleMax: number | undefined;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("_metadata", "metadata");
    this.initRegularAttribute("selection", "selection");
    this.initRegularAttribute("rescale_min", "rescaleMin");
    this.initRegularAttribute("rescale_max", "rescaleMax");
  }

  /** One store per metadata object: a new store starts the layer's tiles over. */
  protected store = memoizeOne(
    (metadata: Record<string, unknown>) => new CommStore(this.model, metadata),
  );

  getTileData = async (
    arr: zarr.Array<zarr.DataType>,
    options: GetTileDataOptions,
  ): Promise<TileData> => {
    const { device, sliceSpec, width, height, signal } = options;
    const chunk = await zarr.get(arr, sliceSpec, { signal });
    const data = chunk.data as Float32Array;
    const texture = device.createTexture({
      format: "r32float",
      width,
      height,
      mipLevels: 1,
      data,
      sampler: {
        minFilter: "nearest",
        magFilter: "nearest",
        addressModeU: "clamp-to-edge",
        addressModeV: "clamp-to-edge",
      },
    });
    return { texture, width, height, byteLength: data.byteLength };
  };

  layerProps() {
    return { id: `${this.model.model_id}` };
  }

  render() {
    if (!this.metadata) {
      return [];
    }
    const rescaleMin = this.rescaleMin ?? 0;
    const rescaleMax = this.rescaleMax ?? 1;

    return new ZarrLayer<TileData>({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      source: this.store(this.metadata),
      selection: this.selection ?? {},
      getTileData: this.getTileData,
      renderTile: (data) => ({
        renderPipeline: [
          { module: CreateTexture, props: { textureName: data.texture } },
          { module: LinearRescale, props: { rescaleMin, rescaleMax } },
        ],
      }),
      onTileUnload: (tile) => tile.content?.texture.destroy(),
      updateTriggers: { renderTile: [rescaleMin, rescaleMax] },
    });
  }
}

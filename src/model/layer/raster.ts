import type { TextureSource } from "@deck.gl/core";
import type { TileLayerProps } from "@deck.gl/geo-layers";
import { TileLayer } from "@deck.gl/geo-layers";
import { BitmapLayer } from "@deck.gl/layers";
import type {
  AffineTilesetLevelOptions,
  MinimalTileData,
  RasterTilesetDescriptor,
} from "@developmentseed/deck.gl-raster";
import {
  AffineTileset,
  AffineTilesetLevel,
  RasterTileLayer,
  TileMatrixSetAdaptor,
} from "@developmentseed/deck.gl-raster";
import type { TileMatrixSet } from "@developmentseed/morecantile";
import type { WidgetModel } from "@jupyter-widgets/base";
import memoizeOne from "memoize-one";
import proj4 from "proj4";
import type { Converter, PROJJSONDefinition } from "proj4/dist/lib/core.js";
import { omitUndefined } from "../../util.js";
import { invoke } from "../dispatch.js";
import { BaseLayerModel } from "./base.js";

// This must be kept in sync with lonboard/layer/_raster.py
const MSG_KIND = "raster-get-tile-data";

type TileResponse =
  | { type: "empty" }
  | { type: "encoded-image"; media_type: string }
  | { error: string };

type TileData = MinimalTileData & {
  image: TextureSource;
};

export class RasterModel extends BaseLayerModel {
  static layerType = "raster";

  protected tileMatrixSet: TileMatrixSet | null | undefined;
  /** Tile grid as affine levels, coarsest first, when there is no tile matrix set */
  protected affineLevels: AffineTilesetLevelOptions[] | null | undefined;
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
    4326: Converter;
    3857: Converter;
  };

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("_tile_matrix_set", "tileMatrixSet");
    this.initRegularAttribute("_affine_levels", "affineLevels");
    this.initCrs("_crs");
    this.initRegularAttribute("_tile_size", "tileSize");
    this.initRegularAttribute("zoom_offset", "zoomOffset");
    this.initRegularAttribute("max_zoom", "maxZoom");
    this.initRegularAttribute("min_zoom", "minZoom");
    this.initRegularAttribute("extent", "extent");
    this.initRegularAttribute("max_cache_size", "maxCacheSize");
    this.initRegularAttribute("debounce_time", "debounceTime");
  }

  /**
   * Initialize the CRS on the model, along with the proj4 converters derived
   * from it.
   *
   * This also watches for changes on the Jupyter model and propagates those
   * changes to this class' internal state.
   *
   * @param   {string}  pythonName  Name of attribute on Python model (usually snake-cased)
   */
  initCrs(pythonName: string) {
    const callback = () => {
      const crs = this.model.get(pythonName);
      this.crs = crs;
      this.converters = crs
        ? {
            4326: proj4(crs, "EPSG:4326"),
            3857: proj4(crs, "EPSG:3857"),
          }
        : undefined;
    };
    callback();

    // Remove all existing change callbacks for this attribute
    this.model.off(`change:${pythonName}`);

    this.model.on(`change:${pythonName}`, callback);

    this.callbacks.set(`change:${pythonName}`, callback);
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
      ...omitUndefined({
        tileSize: this.tileSize,
        zoomOffset: this.zoomOffset,
        maxZoom: this.maxZoom,
        minZoom: this.minZoom,
        extent: this.extent,
        maxCacheSize: this.maxCacheSize,
        debounceTime: this.debounceTime,
      }),
    };
  }

  getTileData = async (
    tile: Parameters<NonNullable<TileLayerProps["getTileData"]>>[0],
  ): Promise<TileData | null> => {
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

    return { image, width: image.width, height: image.height };
  };

  /**
   * The tile grid of `tileMatrixSet` in the source CRS. Memoized because
   * deck.gl-raster reloads every tile when it gets a new descriptor object.
   */
  protected tilesetDescriptor = memoizeOne(
    (
      tileMatrixSet: TileMatrixSet,
      converters: NonNullable<RasterModel["converters"]>,
    ) => new TileMatrixSetAdaptor(tileMatrixSet, projectionFns(converters)),
  );

  /** The tile grid of `affineLevels` in the source CRS. Memoized like `tilesetDescriptor`. */
  protected affineTilesetDescriptor = memoizeOne(
    (
      levels: AffineTilesetLevelOptions[],
      converters: NonNullable<RasterModel["converters"]>,
    ) =>
      new AffineTileset({
        levels: levels.map((level) => new AffineTilesetLevel(level)),
        ...projectionFns(converters),
      }),
  );

  /** The `AffineTileset` for the current `_affine_levels`, or `null` if there are none. */
  affineTileset(): AffineTileset | null {
    const { affineLevels, converters } = this;
    if (!affineLevels || !converters) {
      return null;
    }

    return this.affineTilesetDescriptor(affineLevels, converters);
  }

  renderDescriptor(
    tilesetDescriptor: RasterTilesetDescriptor,
  ): RasterTileLayer<TileData | null> {
    return new RasterTileLayer<TileData | null>({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      tilesetDescriptor,
      getTileData: this.getTileData,
      renderTile: (data) => (data ? { image: data.image } : null),
    });
  }

  render(): TileLayer | RasterTileLayer<TileData | null> {
    const affineTileset = this.affineTileset();
    if (affineTileset) {
      return this.renderDescriptor(affineTileset);
    }

    const tileMatrixSet = this.tileMatrixSet;
    const converters = this.converters;
    if (tileMatrixSet && converters) {
      return this.renderDescriptor(
        this.tilesetDescriptor(tileMatrixSet, converters),
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

/** Projection functions between the source CRS and EPSG:4326 / EPSG:3857 for a tileset descriptor. */
function projectionFns(converters: NonNullable<RasterModel["converters"]>) {
  return {
    projectTo4326: (x: number, y: number): [number, number] =>
      converters[4326].forward([x, y]),
    projectFrom4326: (x: number, y: number): [number, number] =>
      converters[4326].inverse([x, y]),
    projectTo3857: (x: number, y: number): [number, number] =>
      converters[3857].forward([x, y]),
    projectFrom3857: (x: number, y: number): [number, number] =>
      converters[3857].inverse([x, y]),
  };
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

import { TileLayer, TileLayerProps } from "@deck.gl/geo-layers";
import type { Tileset2DProps } from "@deck.gl/geo-layers/dist/tileset-2d";
import { PathLayer } from "@deck.gl/layers";
import { SimpleMeshLayer, SimpleMeshLayerProps } from "@deck.gl/mesh-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";
import GeoTIFF, { fromUrl } from "geotiff";

import { BaseLayerModel } from "./base.js";
import {
  COGTileset2D,
  extractCOGMetadata,
} from "../../cog-tileset/claude-tileset-2d-improved.js";
import { COGMetadata } from "../../cog-tileset/types.js";
import { isDefined } from "../../util.js";

export class SurfaceModel extends BaseLayerModel {
  static layerType = "surface";

  /** vec3. x, y in pixels, z in meters */
  protected positions!: arrow.Vector<arrow.FixedSizeList<arrow.Float32>>;
  /** vec2. 1 to 1 relationship with position. represents the uv on the texture image. 0,0 to 1,1. */
  protected texCoords!: arrow.Vector<arrow.FixedSizeList<arrow.Float32>>;
  /** triples of indices into positions array that create the triangles of the mesh */
  protected triangles!: arrow.Vector<arrow.FixedSizeList<arrow.Uint32>>;

  protected texture?:
    | string
    | {
        width: number;
        height: number;
        data: DataView;
      };
  protected wireframe: SimpleMeshLayerProps["wireframe"];

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initVectorizedAccessor("positions", "positions");
    this.initVectorizedAccessor("tex_coords", "texCoords");
    this.initVectorizedAccessor("triangles", "triangles");

    this.initRegularAttribute("texture", "texture");
    this.initRegularAttribute("wireframe", "wireframe");
  }

  /**
   * Prepare texture input from Python side to something deck.gl can consume.
   *
   * I initially tried to pass in raw texture parameters, but I kept getting
   * WebGL errors. For now, it's simplest to go through an ImageData object.
   */
  prepareTexture(): SimpleMeshLayerProps["texture"] {
    if (!isDefined(this.texture)) {
      return undefined;
    }

    if (typeof this.texture === "string") {
      return this.texture;
    }

    const data: Uint8ClampedArray = new Uint8ClampedArray(
      this.texture.data.buffer,
      this.texture.data.byteOffset,
      this.texture.data.byteLength,
    );

    // @ts-expect-error: ImageData constructor typing
    return new ImageData(data, this.texture.width, this.texture.height);
  }

  layerProps(): SimpleMeshLayerProps {
    return {
      id: this.model.model_id,
      // Dummy data because we're only rendering _one_ instance of this mesh
      // https://github.com/visgl/deck.gl/blob/93111b667b919148da06ff1918410cf66381904f/modules/geo-layers/src/terrain-layer/terrain-layer.ts#L241
      data: [1],
      mesh: {
        indices: {
          // We assume Vector has only one Data chunk
          value: this.triangles.data[0].children[0].values,
          size: 1,
        },
        attributes: {
          POSITION: {
            // We assume Vector has only one Data chunk
            value: this.positions.data[0].children[0].values,
            size: 3,
          },
          TEXCOORD_0: {
            // We assume Vector has only one Data chunk
            value: this.texCoords.data[0].children[0].values,
            size: 2,
          },
        },
      },
      ...(isDefined(this.texture) && { texture: this.prepareTexture() }),
      ...(isDefined(this.wireframe) && { wireframe: this.wireframe }),
      // We're only rendering a single mesh, without instancing
      // https://github.com/visgl/deck.gl/blob/93111b667b919148da06ff1918410cf66381904f/modules/geo-layers/src/terrain-layer/terrain-layer.ts#L244
      _instanced: false,
      // Dummy accessors for the dummy data
      // We place our mesh at the coordinate origin
      getPosition: [0, 0, 0],
      // We give a white color to turn off color mixing with the texture
      getColor: [255, 255, 255],
    };
  }

  render(): SimpleMeshLayer {
    return new SimpleMeshLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
    });
  }
}

export class COGTileModel extends BaseLayerModel {
  static layerType = "cog-tile";

  protected data!: string;
  protected tileSize: TileLayerProps["tileSize"];
  protected zoomOffset: TileLayerProps["zoomOffset"];
  protected maxZoom: TileLayerProps["maxZoom"];
  protected minZoom: TileLayerProps["minZoom"];
  protected extent: TileLayerProps["extent"];
  protected maxCacheSize: TileLayerProps["maxCacheSize"];
  protected maxCacheByteSize: TileLayerProps["maxCacheByteSize"];
  protected refinementStrategy: TileLayerProps["refinementStrategy"];
  protected maxRequests: TileLayerProps["maxRequests"];

  protected tiff?: GeoTIFF;
  protected cogMetadata?: COGMetadata;

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
  }

  async asyncInit() {
    console.log("Loading COG from URL:", this.data);
    const tiff = await fromUrl(this.data);
    const metadata = await extractCOGMetadata(tiff);

    this.tiff = tiff;
    this.cogMetadata = metadata;
  }

  async loadSubModels() {
    await this.asyncInit();
  }

  layerProps(): TileLayerProps {
    // Create a factory class that wraps COGTileset2D with the metadata
    if (!this.cogMetadata) {
      throw new Error("COG metadata not loaded. Call asyncInit first.");
    }

    // Capture cogMetadata in closure with proper type
    const cogMetadata: COGMetadata = this.cogMetadata;

    class COGTilesetWrapper extends COGTileset2D {
      constructor(opts: Tileset2DProps) {
        super(cogMetadata, opts);
      }
    }

    return {
      id: this.model.model_id,
      data: this.data,
      TilesetClass: COGTilesetWrapper,
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

  render(): TileLayer[] {
    // Capture cogMetadata in closure
    const metadata = this.cogMetadata;

    const layer = new TileLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),

      renderSubLayers: (props) => {
        const { tile } = props;
        console.log("Rendering COG tile with props:");
        console.log(props);

        // Get projected bounds from tile data
        // getTileMetadata returns data that includes projectedBounds
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const projectedBounds = (tile as any)?.projectedBounds;

        if (!projectedBounds || !metadata) {
          return [];
        }

        // Project bounds from image CRS to WGS84
        const { topLeft, topRight, bottomLeft, bottomRight } = projectedBounds;

        const topLeftWgs84 = metadata.projectToWgs84.forward(topLeft);
        const topRightWgs84 = metadata.projectToWgs84.forward(topRight);
        const bottomRightWgs84 = metadata.projectToWgs84.forward(bottomRight);
        const bottomLeftWgs84 = metadata.projectToWgs84.forward(bottomLeft);

        // Create a closed path around the tile bounds
        const path = [
          topLeftWgs84,
          topRightWgs84,
          bottomRightWgs84,
          bottomLeftWgs84,
          topLeftWgs84, // Close the path
        ];

        console.log("Tile bounds path (WGS84):", path);

        return [
          new PathLayer({
            id: `${tile.id}-bounds`,
            data: [{ path }],
            getPath: (d) => d.path,
            getColor: [255, 0, 0, 255], // Red
            getWidth: 2,
            widthUnits: "pixels",
            pickable: false,
          }),
        ];
      },
    });
    return [layer];
  }
}

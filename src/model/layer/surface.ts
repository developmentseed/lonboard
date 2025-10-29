import { SimpleMeshLayer, SimpleMeshLayerProps } from "@deck.gl/mesh-layers";
import type { WidgetModel } from "@jupyter-widgets/base";
import * as arrow from "apache-arrow";

import { isDefined } from "../../util.js";
import { BaseLayerModel } from "../base-layer.js";

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

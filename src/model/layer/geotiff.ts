import { SimpleMeshLayer, SimpleMeshLayerProps } from "@deck.gl/mesh-layers";
import { reprojection } from "@developmentseed/deck.gl-raster";
import type { WidgetModel } from "@jupyter-widgets/base";
import proj4 from "proj4";
import type { PROJJSONDefinition } from "proj4/dist/lib/core.js";
import type Projection from "proj4/dist/lib/Proj.js";

import { BaseLayerModel } from "./base.js";
import { isDefined } from "../../util.js";

const OGC_84: PROJJSONDefinition = {
  $schema: "https://proj.org/schemas/v0.7/projjson.schema.json",
  type: "GeographicCRS",
  name: "WGS 84 (CRS84)",
  datum_ensemble: {
    name: "World Geodetic System 1984 ensemble",
    members: [
      {
        name: "World Geodetic System 1984 (Transit)",
        id: { authority: "EPSG", code: 1166 },
      },
      {
        name: "World Geodetic System 1984 (G730)",
        id: { authority: "EPSG", code: 1152 },
      },
      {
        name: "World Geodetic System 1984 (G873)",
        id: { authority: "EPSG", code: 1153 },
      },
      {
        name: "World Geodetic System 1984 (G1150)",
        id: { authority: "EPSG", code: 1154 },
      },
      {
        name: "World Geodetic System 1984 (G1674)",
        id: { authority: "EPSG", code: 1155 },
      },
      {
        name: "World Geodetic System 1984 (G1762)",
        id: { authority: "EPSG", code: 1156 },
      },
      {
        name: "World Geodetic System 1984 (G2139)",
        id: { authority: "EPSG", code: 1309 },
      },
    ],
    ellipsoid: {
      name: "WGS 84",
      semi_major_axis: 6378137,
      inverse_flattening: 298.257223563,
    },
    accuracy: "2.0",
    id: { authority: "EPSG", code: 6326 },
  },
  coordinate_system: {
    subtype: "ellipsoidal",
    axis: [
      {
        name: "Geodetic longitude",
        abbreviation: "Lon",
        direction: "east",
        unit: "degree",
      },
      {
        name: "Geodetic latitude",
        abbreviation: "Lat",
        direction: "north",
        unit: "degree",
      },
    ],
  },
  scope: "Not known.",
  area: "World.",
  bbox: {
    south_latitude: -90,
    west_longitude: -180,
    north_latitude: 90,
    east_longitude: 180,
  },
  // @ts-expect-error - proj4 types are incomplete
  id: { authority: "OGC", code: "CRS84" },
};

export class GeotiffModel extends BaseLayerModel {
  static layerType = "geotiff";

  protected sourceProjection!: Projection;
  protected geotransform!: [number, number, number, number, number, number];
  protected width!: number;
  protected height!: number;

  protected texture?:
    | string
    | {
        width: number;
        height: number;
        data: DataView;
      };
  protected wireframe: SimpleMeshLayerProps["wireframe"];

  protected reprojectionMesh: reprojection.RasterReprojector;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("source_projection", "sourceProjection");
    this.initRegularAttribute("geotransform", "geotransform");
    this.initRegularAttribute("texture", "texture");
    this.initRegularAttribute("wireframe", "wireframe");
    this.initRegularAttribute("width", "width");
    this.initRegularAttribute("height", "height");

    const reprojectors = createReprojectionFunctions(
      this.geotransform,
      this.sourceProjection,
    );

    console.time("RasterReprojector initialization");
    const reprojectionMesh = new reprojection.RasterReprojector(
      reprojectors,
      this.width,
      this.height,
    );
    console.timeEnd("RasterReprojector initialization");

    console.time("RasterReprojector mesh generation");
    reprojectionMesh.run(0.125);
    console.timeEnd("RasterReprojector mesh generation");

    this.reprojectionMesh = reprojectionMesh;
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

  createReprojectors(): reprojection.ReprojectionFns {
    return createReprojectionFunctions(
      this.geotransform,
      this.sourceProjection,
    );
  }

  layerProps(): SimpleMeshLayerProps {
    const mesh = buildDeckMeshFromDelatin(this.reprojectionMesh);
    return {
      id: this.model.model_id,
      // Dummy data because we're only rendering _one_ instance of this mesh
      // https://github.com/visgl/deck.gl/blob/93111b667b919148da06ff1918410cf66381904f/modules/geo-layers/src/terrain-layer/terrain-layer.ts#L241
      data: [1],
      mesh,
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

function createReprojectionFunctions(
  geotransform: [number, number, number, number, number, number],
  sourceProjection: Projection,
): reprojection.ReprojectionFns {
  const converter = proj4(sourceProjection, OGC_84);

  const inverseGeotransform =
    reprojection.affine.invertGeoTransform(geotransform);
  return {
    pixelToInputCRS: (x: number, y: number) =>
      reprojection.affine.applyAffine(x, y, geotransform),
    inputCRSToPixel: (x: number, y: number) =>
      reprojection.affine.applyAffine(x, y, inverseGeotransform),
    forwardReproject: (x: number, y: number) =>
      converter.forward([x, y], false),
    inverseReproject: (x: number, y: number) =>
      converter.inverse([x, y], false),
  };
}

function buildDeckMeshFromDelatin(reprojector: reprojection.RasterReprojector) {
  const vertexCount = reprojector.uvs.length / 2;

  const positions = new Float32Array(vertexCount * 3);
  const texCoords = new Float32Array(reprojector.uvs);

  for (let i = 0; i < vertexCount; i++) {
    positions[i * 3 + 0] = reprojector.exactOutputPositions[i * 2];
    positions[i * 3 + 1] = reprojector.exactOutputPositions[i * 2 + 1];
    positions[i * 3 + 2] = 0.0;
  }

  const indices = new Uint32Array(reprojector.triangles);

  return {
    indices: {
      value: indices,
      size: 1,
    },
    attributes: {
      POSITION: { value: positions, size: 3 },
      TEXCOORD_0: { value: texCoords, size: 2 },
    },
  };
}

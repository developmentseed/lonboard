/**
 * COGTileset2D - Improved Implementation with Frustum Culling
 *
 * This version properly implements frustum culling and bounding volume calculations
 * following the pattern from deck.gl's OSM tile indexing.
 */

import { Viewport, WebMercatorViewport } from "@deck.gl/core";
import { _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import type { Tileset2DProps } from "@deck.gl/geo-layers/dist/tileset-2d";
import type { ZRange } from "@deck.gl/geo-layers/dist/tileset-2d/types";
import { Matrix4 } from "@math.gl/core";
import { GeoTIFF, GeoTIFFImage } from "geotiff";
import proj4 from "proj4";

import { getTileIndices } from "./cog-tile-2d-traversal";
import type { COGMetadata, COGTileIndex, COGOverview, Bounds } from "./types";

const OGC_84 = {
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
  id: { authority: "OGC", code: "CRS84" },
};

/**
 * Extract affine geotransform from a GeoTIFF image.
 *
 * Returns a 6-element array in Python `affine` package ordering:
 * [a, b, c, d, e, f] where:
 * - x_geo = a * col + b * row + c
 * - y_geo = d * col + e * row + f
 *
 * This is NOT GDAL ordering, which is [c, a, b, f, d, e].
 */
function extractGeotransform(
  image: GeoTIFFImage,
): [number, number, number, number, number, number] {
  const origin = image.getOrigin();
  const resolution = image.getResolution();

  // origin: [x, y, z]
  // resolution: [x_res, y_res, z_res]

  // Check for rotation/skew in the file directory
  const fileDirectory = image.getFileDirectory();
  const modelTransformation = fileDirectory.ModelTransformation;

  let b = 0; // row rotation
  let d = 0; // column rotation

  if (modelTransformation && modelTransformation.length >= 16) {
    // ModelTransformation is a 4x4 matrix in row-major order
    // [0  1  2  3 ]   [a  b  0  c]
    // [4  5  6  7 ] = [d  e  0  f]
    // [8  9  10 11]   [0  0  1  0]
    // [12 13 14 15]   [0  0  0  1]
    b = modelTransformation[1];
    d = modelTransformation[4];
  }

  // Return in affine package ordering: [a, b, c, d, e, f]
  return [
    resolution[0], // a: pixel width
    b, // b: row rotation
    origin[0], // c: x origin
    d, // d: column rotation
    resolution[1], // e: pixel height (often negative)
    origin[1], // f: y origin
  ];
}

/**
 * Extract COG metadata
 */
export async function extractCOGMetadata(tiff: GeoTIFF): Promise<COGMetadata> {
  const image = await tiff.getImage();

  const width = image.getWidth();
  const height = image.getHeight();
  const tileWidth = image.getTileWidth();
  const tileHeight = image.getTileHeight();

  const tilesX = Math.ceil(width / tileWidth);
  const tilesY = Math.ceil(height / tileHeight);

  const bbox = image.getBoundingBox();
  const geoKeys = image.getGeoKeys();
  const projectionCode: number | null =
    geoKeys.ProjectedCSTypeGeoKey || geoKeys.GeographicTypeGeoKey || null;
  const projection = projectionCode ? `EPSG:${projectionCode}` : null;

  // Extract geotransform from full-resolution image
  // Only the top-level IFD has geo keys, so we'll derive overviews from this
  const baseGeotransform = extractGeotransform(image);

  // Overviews **in COG order**, from finest to coarsest (we'll reverse the
  // array later)
  const overviews: COGOverview[] = [];
  const imageCount = await tiff.getImageCount();

  // Full resolution image (GeoTIFF index 0)
  overviews.push({
    geoTiffIndex: 0,
    width,
    height,
    tilesX,
    tilesY,
    scaleFactor: 1,
    geotransform: baseGeotransform,
    // TODO: combine these two properties into one
    level: imageCount - 1, // Coarsest level number
    z: imageCount - 1,
  });

  for (let i = 1; i < imageCount; i++) {
    const overview = await tiff.getImage(i);
    const overviewWidth = overview.getWidth();
    const overviewHeight = overview.getHeight();
    const overviewTileWidth = overview.getTileWidth();
    const overviewTileHeight = overview.getTileHeight();

    const scaleFactor = Math.round(width / overviewWidth);

    // Derive geotransform for this overview by scaling pixel size
    // [a, b, c, d, e, f] where a and e are pixel dimensions
    const overviewGeotransform: [
      number,
      number,
      number,
      number,
      number,
      number,
    ] = [
      baseGeotransform[0] * scaleFactor, // a: scaled pixel width
      baseGeotransform[1] * scaleFactor, // b: scaled row rotation
      baseGeotransform[2], // c: same x origin
      baseGeotransform[3] * scaleFactor, // d: scaled column rotation
      baseGeotransform[4] * scaleFactor, // e: scaled pixel height (typically negative)
      baseGeotransform[5], // f: same y origin
    ];

    overviews.push({
      geoTiffIndex: i,
      width: overviewWidth,
      height: overviewHeight,
      tilesX: Math.ceil(overviewWidth / overviewTileWidth),
      tilesY: Math.ceil(overviewHeight / overviewTileHeight),
      scaleFactor,
      geotransform: overviewGeotransform,
      // TODO: combine these two properties into one
      level: imageCount - 1 - i,
      z: imageCount - 1 - i,
    });
  }

  // Reverse to TileMatrixSet order: coarsest (0) → finest (n)
  overviews.reverse();

  const sourceProjection = await getProjjson(projectionCode);
  const projectToWgs84 = proj4(sourceProjection, OGC_84);
  const projectTo3857 = proj4(sourceProjection, "EPSG:3857");

  return {
    width,
    height,
    tileWidth,
    tileHeight,
    tilesX,
    tilesY,
    bbox: [bbox[0], bbox[1], bbox[2], bbox[3]],
    projection,
    projectToWgs84,
    projectTo3857,
    overviews,
    image: tiff,
  };
}

async function getProjjson(projectionCode: number | null) {
  const url = `https://epsg.io/${projectionCode}.json`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch projection data from ${url}`);
  }
  const data = await response.json();
  return data;
}

const viewport = new WebMercatorViewport({
  height: 500,
  width: 845,
  latitude: 40.88775942857086,
  longitude: -73.20197979318772,
  zoom: 11.294596276534985,
});

/**
 * COGTileset2D with proper frustum culling
 */
export class COGTileset2D extends Tileset2D {
  private cogMetadata: COGMetadata;

  constructor(cogMetadata: COGMetadata, opts: Tileset2DProps) {
    super(opts);
    this.cogMetadata = cogMetadata;
  }

  /**
   * Get tile indices visible in viewport
   * Uses frustum culling similar to OSM implementation
   *
   * Overviews follow TileMatrixSet ordering: index 0 = coarsest, higher = finer
   */
  getTileIndices(opts: {
    viewport: Viewport;
    maxZoom?: number;
    minZoom?: number;
    zRange: ZRange | null;
    modelMatrix?: Matrix4;
    modelMatrixInverse?: Matrix4;
  }): COGTileIndex[] {
    console.log("Called getTileIndices", opts);
    const tileIndices = getTileIndices(this.cogMetadata, opts);
    console.log("Visible tile indices:", tileIndices);

    // return [
    //   { x: 0, y: 0, z: 0 },
    //   { x: 0, y: 0, z: 1 },
    //   { x: 1, y: 1, z: 2 },
    //   { x: 1, y: 2, z: 3 },
    //   { x: 2, y: 1, z: 3 },
    //   { x: 2, y: 2, z: 3 },
    //   { x: 3, y: 1, z: 3 },
    // ]; // Temporary override for testing
    return tileIndices;
  }

  getTileId(index: COGTileIndex): string {
    return `${index.x}-${index.y}-${index.z}`;
  }

  getParentIndex(index: COGTileIndex): COGTileIndex {
    if (index.z === 0) {
      // Already at coarsest level
      return index;
    }

    const currentOverview = this.cogMetadata.overviews[index.z];
    const parentOverview = this.cogMetadata.overviews[index.z - 1];

    const scaleFactor =
      currentOverview.scaleFactor / parentOverview.scaleFactor;

    return {
      x: Math.floor(index.x / scaleFactor),
      y: Math.floor(index.y / scaleFactor),
      z: index.z - 1,
    };
  }

  getTileZoom(index: COGTileIndex): number {
    return index.z;
  }

  getTileMetadata(index: COGTileIndex): Record<string, unknown> {
    const { x, y, z } = index;
    const { overviews, tileWidth, tileHeight } = this.cogMetadata;
    const overview = overviews[z];

    // Use geotransform to calculate tile bounds
    // geotransform: [a, b, c, d, e, f] where:
    // x_geo = a * col + b * row + c
    // y_geo = d * col + e * row + f
    const [a, b, c, d, e, f] = overview.geotransform;

    // Calculate pixel coordinates for this tile's extent
    const pixelMinCol = x * tileWidth;
    const pixelMinRow = y * tileHeight;
    const pixelMaxCol = (x + 1) * tileWidth;
    const pixelMaxRow = (y + 1) * tileHeight;

    // Calculate the four corners of the tile in geographic coordinates
    const topLeft = [
      a * pixelMinCol + b * pixelMinRow + c,
      d * pixelMinCol + e * pixelMinRow + f,
    ];
    const topRight = [
      a * pixelMaxCol + b * pixelMinRow + c,
      d * pixelMaxCol + e * pixelMinRow + f,
    ];
    const bottomLeft = [
      a * pixelMinCol + b * pixelMaxRow + c,
      d * pixelMinCol + e * pixelMaxRow + f,
    ];
    const bottomRight = [
      a * pixelMaxCol + b * pixelMaxRow + c,
      d * pixelMaxCol + e * pixelMaxRow + f,
    ];

    // Return the projected bounds as four corners
    // This preserves rotation/skew information
    const projectedBounds = {
      topLeft,
      topRight,
      bottomLeft,
      bottomRight,
    };

    // Also compute axis-aligned bounding box for compatibility
    const bounds: Bounds = [
      Math.min(topLeft[0], topRight[0], bottomLeft[0], bottomRight[0]),
      Math.min(topLeft[1], topRight[1], bottomLeft[1], bottomRight[1]),
      Math.max(topLeft[0], topRight[0], bottomLeft[0], bottomRight[0]),
      Math.max(topLeft[1], topRight[1], bottomLeft[1], bottomRight[1]),
    ];

    return {
      bounds,
      projectedBounds,
      tileWidth,
      tileHeight,
      overview,
    };
  }
}

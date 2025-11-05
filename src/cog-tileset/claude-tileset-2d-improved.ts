/**
 * COGTileset2D - Improved Implementation with Frustum Culling
 *
 * This version properly implements frustum culling and bounding volume calculations
 * following the pattern from deck.gl's OSM tile indexing.
 */

import { Viewport } from "@deck.gl/core";
import { _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import type { Tileset2DProps } from "@deck.gl/geo-layers/dist/tileset-2d";
import type { ZRange } from "@deck.gl/geo-layers/dist/tileset-2d/types";
import { Matrix4 } from "@math.gl/core";
import { GeoTIFF } from "geotiff";
import proj4 from "proj4";

import { getTileIndices } from "./cog-tile-2d-traversal";
import type { COGMetadata, COGTileIndex, COGOverview } from "./types";

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

    overviews.push({
      geoTiffIndex: i,
      width: overviewWidth,
      height: overviewHeight,
      tilesX: Math.ceil(overviewWidth / overviewTileWidth),
      tilesY: Math.ceil(overviewHeight / overviewTileHeight),
      scaleFactor: Math.round(width / overviewWidth),
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
    console.log("Getting tile indices with COGTileset2D");
    console.log(opts);
    const tileIndices = getTileIndices(this.cogMetadata, opts);
    console.log("Visible tile indices:");
    console.log(tileIndices);
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
    const overview = this.cogMetadata.overviews[index.z];
    return {
      bounds: index.bounds,
      level: index.level,
      tileWidth: this.cogMetadata.tileWidth,
      tileHeight: this.cogMetadata.tileHeight,
      overview,
    };
  }
}

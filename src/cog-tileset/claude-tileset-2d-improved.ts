/**
 * COGTileset2D - Improved Implementation with Frustum Culling
 *
 * This version properly implements frustum culling and bounding volume calculations
 * following the pattern from deck.gl's OSM tile indexing.
 */

import { Viewport, WebMercatorViewport, _GlobeViewport } from "@deck.gl/core";
import { _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import type { Bounds, ZRange } from "@deck.gl/geo-layers/dist/tileset-2d/types";
import {
  CullingVolume,
  Plane,
  AxisAlignedBoundingBox,
  makeOrientedBoundingBoxFromPoints,
} from "@math.gl/culling";
import { GeoTIFF } from "geotiff";

import type { COGMetadata, COGTileIndex, COGOverview } from "./types";

/**
 * Extract COG metadata
 */
async function extractCOGMetadata(tiff: GeoTIFF): Promise<COGMetadata> {
  const image = await tiff.getImage();

  const width = image.getWidth();
  const height = image.getHeight();
  const tileWidth = image.getTileWidth();
  const tileHeight = image.getTileHeight();

  const tilesX = Math.ceil(width / tileWidth);
  const tilesY = Math.ceil(height / tileHeight);

  const bbox = image.getBoundingBox();
  const geoKeys = image.getGeoKeys();
  const projection =
    geoKeys.ProjectedCSTypeGeoKey || geoKeys.GeographicTypeGeoKey
      ? `EPSG:${geoKeys.ProjectedCSTypeGeoKey || geoKeys.GeographicTypeGeoKey}`
      : null;

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

  return {
    width,
    height,
    tileWidth,
    tileHeight,
    tilesX,
    tilesY,
    bbox: [bbox[0], bbox[1], bbox[2], bbox[3]],
    projection,
    overviews,
    image: tiff,
  };
}

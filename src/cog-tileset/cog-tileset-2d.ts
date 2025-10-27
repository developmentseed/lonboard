import { Viewport } from "@deck.gl/core";
import { _Tileset2D as Tileset2D } from "@deck.gl/geo-layers";
import { TileIndex, ZRange } from "@deck.gl/geo-layers/dist/tileset-2d/types";
import { Matrix4 } from "@math.gl/core";

import { getOSMTileIndices } from "./tile-2d-traversal";

type Bounds = [minX: number, minY: number, maxX: number, maxY: number];

export class COGTileset2D extends Tileset2D {
  getTileIndices({
    viewport,
    maxZoom,
    minZoom,
    zRange,
    tileSize,
    modelMatrix,
    modelMatrixInverse,
    zoomOffset,
  }: {
    viewport: Viewport;
    maxZoom?: number;
    minZoom?: number;
    zRange: ZRange | null;
    tileSize?: number;
    modelMatrix?: Matrix4;
    modelMatrixInverse?: Matrix4;
    zoomOffset?: number;
  }): TileIndex[] {
    const { extent } = this.opts;
  }
}

const TILE_SIZE = 512;

/**
 * Returns all tile indices in the current viewport. If the current zoom level is smaller
 * than minZoom, return an empty array. If the current zoom level is greater than maxZoom,
 * return tiles that are on maxZoom.
 */

export function getTileIndices({
  viewport,
  maxZoom,
  minZoom,
  zRange,
  extent,
  tileSize = TILE_SIZE,
  modelMatrix,
  modelMatrixInverse,
  zoomOffset = 0,
}: {
  viewport: Viewport;
  maxZoom?: number;
  minZoom?: number;
  zRange: ZRange | null;
  extent?: Bounds;
  tileSize?: number;
  modelMatrix?: Matrix4;
  modelMatrixInverse?: Matrix4;
  zoomOffset?: number;
}) {
  let z =
    Math.round(viewport.zoom + Math.log2(TILE_SIZE / tileSize)) + zoomOffset;
  if (typeof minZoom === "number" && Number.isFinite(minZoom) && z < minZoom) {
    if (!extent) {
      return [];
    }
    z = minZoom;
  }
  if (typeof maxZoom === "number" && Number.isFinite(maxZoom) && z > maxZoom) {
    z = maxZoom;
  }
  return getOSMTileIndices(viewport, z, zRange, extent);
}

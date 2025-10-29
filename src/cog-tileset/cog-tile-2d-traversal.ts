import { Viewport } from "@deck.gl/core";
import {
  CullingVolume,
  AxisAlignedBoundingBox,
  makeOrientedBoundingBoxFromPoints,
} from "@math.gl/culling";

import { Bounds, ZRange } from "./types";
import type { COGMetadata, COGOverview } from "./types";

// for calculating bounding volume of a tile in a non-web-mercator viewport
const REF_POINTS_5 = [
  [0.5, 0.5],
  [0, 0],
  [0, 1],
  [1, 0],
  [1, 1],
]; // 4 corners and center

/**
 * COG Tile Node - similar to OSMNode but for COG's tile structure
 *
 * Uses TileMatrixSet ordering where: index 0 = coarsest, higher = finer.
 * In this ordering, z === level (both increase with detail).
 */
export class COGTileNode {
  /** Index across a row */
  x: number;
  /** Index down a column */
  y: number;
  /** TileMatrixSet-style zoom index (higher = finer detail) */
  z: number;

  private cogMetadata: COGMetadata;

  private childVisible?: boolean;
  private selected?: boolean;
  /** A cache of the children of this node. */
  private _children?: COGTileNode[];

  constructor(x: number, y: number, z: number, cogMetadata: COGMetadata) {
    this.x = x;
    this.y = y;
    this.z = z;
    this.cogMetadata = cogMetadata;
  }

  /** Get overview info for this tile's z level */
  get overview(): COGOverview {
    return this.cogMetadata.overviews[this.z];
  }

  /** Get the children of this node. */
  get children(): COGTileNode[] {
    if (!this._children) {
      const maxZ = this.cogMetadata.overviews.length - 1;
      if (this.z >= maxZ) {
        // Already at finest resolution, no children
        return [];
      }

      // In TileMatrixSet ordering: refine to z + 1 (finer detail)
      const childZ = this.z + 1;
      const parentOverview = this.overview;
      const childOverview = this.cogMetadata.overviews[childZ];

      // Calculate scale factor between levels
      const scaleFactor =
        parentOverview.scaleFactor / childOverview.scaleFactor;

      // Generate child tiles
      this._children = [];
      for (let dy = 0; dy < scaleFactor; dy++) {
        for (let dx = 0; dx < scaleFactor; dx++) {
          const childX = this.x * scaleFactor + dx;
          const childY = this.y * scaleFactor + dy;

          // Only create child if it's within bounds
          // Some tiles on the edges might not need to be created at higher
          // resolutions (higher map zoom level)
          if (childX < childOverview.tilesX && childY < childOverview.tilesY) {
            this._children.push(
              new COGTileNode(childX, childY, childZ, this.cogMetadata),
            );
          }
        }
      }
    }
    return this._children;
  }

  /**
   * Update tile visibility using frustum culling
   * This follows the pattern from OSMNode
   */
  update(params: {
    viewport: Viewport;
    project: ((xyz: number[]) => number[]) | null;
    cullingVolume: CullingVolume;
    elevationBounds: ZRange;
    minZ: number; // Minimum z (coarsest acceptable)
    maxZ: number; // Maximum z (finest acceptable)
    bounds?: Bounds; // In COG's coordinate space
  }): boolean {
    const {
      viewport,
      cullingVolume,
      elevationBounds,
      minZ,
      maxZ,
      bounds,
      project,
    } = params;

    // Get bounding volume for this tile
    const boundingVolume = this.getBoundingVolume(elevationBounds, project);

    // Note: this is a part of the upstream code because they have _generic_
    // tiling systems, where the client doesn't know whether a given xyz tile
    // actually exists. So the idea of `bounds` is to avoid even trying to fetch
    // tiles that the user doesn't care about (think oceans)
    //
    // But in our case, we have known bounds from the COG metadata. So the tiles
    // are explicitly constructed to match only tiles that exist.

    // Check if tile is within user-specified bounds
    // if (bounds && !this.insideBounds(bounds)) {
    //   return false;
    // }

    // Check if tile is visible in frustum
    const isInside = cullingVolume.computeVisibility(boundingVolume);
    if (isInside < 0) {
      return false;
    }

    // Avoid loading overlapping tiles
    if (!this.childVisible) {
      let { z } = this;

      if (z < maxZ && z >= minZ) {
        // Adjust LOD based on distance from camera
        // If tile is far from camera, accept coarser resolution (lower z)
        const distance =
          (boundingVolume.distanceTo(viewport.cameraPosition) *
            viewport.scale) /
          viewport.height;
        z += Math.floor(Math.log2(distance));
      }

      if (z >= maxZ) {
        // LOD is acceptable
        this.selected = true;
        return true;
      }
    }

    // LOD is not enough, recursively test child tiles
    this.selected = false;
    this.childVisible = true;

    const children = this.children;
    // NOTE: this deviates from upstream; we could move to the upstream code if
    // we pass in maxZ correctly I think
    if (children.length === 0) {
      // No children available (at finest resolution), select this tile
      this.selected = true;
      return true;
    }

    for (const child of children) {
      child.update(params);
    }
    return true;
  }

  /**
   * Collect all selected tiles
   */
  getSelected(result: COGTileNode[] = []): COGTileNode[] {
    if (this.selected) {
      result.push(this);
    }
    if (this._children) {
      for (const node of this._children) {
        node.getSelected(result);
      }
    }
    return result;
  }

  /**
   * Calculate bounding volume for frustum culling
   */
  getBoundingVolume(
    zRange: ZRange,
    project: ((xyz: number[]) => number[]) | null,
  ) {
    const overview = this.overview;
    const { bbox, tileWidth, tileHeight } = this.cogMetadata;

    const cogWidth = bbox[2] - bbox[0];
    const cogHeight = bbox[3] - bbox[1];

    const tileGeoWidth = cogWidth / overview.tilesX;
    const tileGeoHeight = cogHeight / overview.tilesY;

    const tileMinX = bbox[0] + this.x * tileGeoWidth;
    const tileMinY = bbox[1] + this.y * tileGeoHeight;
    const tileMaxX = tileMinX + tileGeoWidth;
    const tileMaxY = tileMinY + tileGeoHeight;

    if (project) {
      // Custom projection (e.g., GlobeView)
      // Sample points on tile to create bounding volume
      const refPoints = [
        [0.5, 0.5], // center
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1], // corners
      ];

      const refPointPositions: number[][] = [];
      for (const [fx, fy] of refPoints) {
        const geoX = tileMinX + fx * tileGeoWidth;
        const geoY = tileMinY + fy * tileGeoHeight;

        // Convert from COG coordinates to lng/lat
        // This assumes COG is in Web Mercator - adjust for other projections
        const lngLat = this.cogCoordsToLngLat([geoX, geoY]);
        lngLat[2] = zRange[0];
        refPointPositions.push(project(lngLat));

        if (zRange[0] !== zRange[1]) {
          lngLat[2] = zRange[1];
          refPointPositions.push(project(lngLat));
        }
      }

      return makeOrientedBoundingBoxFromPoints(refPointPositions);
    }

    // Web Mercator projection
    // Assuming COG is already in Web Mercator (EPSG:3857)
    // Convert from meters to deck.gl's common space (world units)
    const WORLD_SIZE = 512; // deck.gl's world size
    const METERS_PER_WORLD = 40075017; // Earth circumference at equator

    const worldMinX = (tileMinX / METERS_PER_WORLD) * WORLD_SIZE;
    const worldMaxX = (tileMaxX / METERS_PER_WORLD) * WORLD_SIZE;

    // Y is flipped in deck.gl's common space
    const worldMinY = WORLD_SIZE - (tileMaxY / METERS_PER_WORLD) * WORLD_SIZE;
    const worldMaxY = WORLD_SIZE - (tileMinY / METERS_PER_WORLD) * WORLD_SIZE;

    return new AxisAlignedBoundingBox(
      [worldMinX, worldMinY, zRange[0]],
      [worldMaxX, worldMaxY, zRange[1]],
    );
  }

  /**
   * Convert COG coordinates to lng/lat
   * This is a placeholder - needs proper projection library (proj4js)
   */
  private cogCoordsToLngLat([x, y]: [number, number]): number[] {
    // For Web Mercator (EPSG:3857)
    const R = 6378137; // Earth radius
    const lng = (x / R) * (180 / Math.PI);
    const lat =
      (Math.PI / 2 - 2 * Math.atan(Math.exp(-y / R))) * (180 / Math.PI);
    return [lng, lat, 0];
  }
}

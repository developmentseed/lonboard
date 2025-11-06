/**
 * This file implements tile traversal for generic 2D tilesets defined by COG
 * tile layouts.
 *
 * The main algorithm works as follows:
 * 1. Start at the root tile(s) (z=0, covers the entire image, but not
 *    necessarily the whole world)
 * 2. Test if each tile is visible using viewport frustum culling
 * 3. For visible tiles, compute distance-based LOD (Level of Detail)
 * 4. If LOD is insufficient, recursively subdivide into 4 child tiles
 * 5. Select tiles at appropriate zoom levels based on distance from camera
 *
 * The result is a set of tiles at varying zoom levels that efficiently
 * cover the visible area with appropriate detail.
 */

import { _GlobeViewport, assert, Viewport } from "@deck.gl/core";
import { AxisAlignedBoundingBox, CullingVolume, Plane } from "@math.gl/culling";

import type {
  Bounds,
  COGMetadata,
  COGOverview,
  COGTileIndex,
  ZRange,
} from "./types";

/**
 * The size of the entire world in deck.gl's common coordinate space.
 *
 * The world always spans [0, 512] in both X and Y in Web Mercator common space.
 *
 * The origin (0,0) is at the top-left corner, and (512,512) is at the
 * bottom-right.
 */
const WORLD_SIZE = 512;

// Reference points used to sample tile boundaries for bounding volume
// calculation.
//
// In upstream deck.gl code, such reference points are only used in non-Web
// Mercator projections because the OSM tiling scheme is designed for Web
// Mercator and the OSM tile extents are already in Web Mercator projection. So
// using Axis-Aligned bounding boxes based on tile extents is sufficient for
// frustum culling in Web Mercator viewports.
//
// In upstream code these reference points are used for Globe View where the OSM
// tile indices _projected into longitude-latitude bounds in Globe View space_
// are no longer axis-aligned, and oriented bounding boxes must be used instead.
//
// In the context of generic tiling grids which are often not in Web Mercator
// projection, we must use the reference points approach because the grid tiles
// will never be exact axis aligned boxes in Web Mercator space.

// For most tiles: sample 4 corners and center (5 points total)
const REF_POINTS_5 = [
  [0.5, 0.5], // center
  [0, 0], // top-left
  [0, 1], // bottom-left
  [1, 0], // top-right
  [1, 1], // bottom-right
];

// For higher detail: add 4 edge midpoints (9 points total)
const REF_POINTS_9 = REF_POINTS_5.concat([
  [0, 0.5], // left edge
  [0.5, 0], // top edge
  [1, 0.5], // right edge
  [0.5, 1], // bottom edge
]);

/**
 * COG Tile Node - similar to OSMNode but for COG's tile structure.
 *
 * Represents a single tile in the COG internal tiling pyramid.
 *
 * COG tile nodes use the following coordinate system:
 *
 * - x: tile column (0 to COGOverview.tilesX, left to right)
 * - y: tile row (0 to COGOverview.tilesY, top to bottom)
 * - z: overview level. This uses TileMatrixSet ordering where: 0 = coarsest, higher = finer
 */
export class COGTileNode {
  /** Index across a row */
  x: number;
  /** Index down a column */
  y: number;
  /** TileMatrixSet-style zoom index (higher = finer detail) */
  z: number;

  private cogMetadata: COGMetadata;

  /**
   * Flag indicating whether any descendant of this tile is visible.
   *
   * Used to prevent loading parent tiles when children are visible (avoids
   * overdraw).
   */
  private childVisible?: boolean;

  /**
   * Flag indicating this tile should be rendered
   *
   * Set to `true` when this is the appropriate LOD for its distance from camera.
   */
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
    /** Minimum (coarsest) COG overview level */
    minZ: number;
    /** Maximum (finest) COG overview level */
    maxZ?: number;
  }): boolean {
    const {
      viewport,
      cullingVolume,
      elevationBounds,
      minZ,
      maxZ = this.cogMetadata.overviews.length - 1,
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
    console.log(
      `Tile ${this.x},${this.y},${this.z} frustum check: ${isInside} (${isInside < 0 ? "CULLED" : "VISIBLE"})`,
    );
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
   * Collect all tiles marked as selected in the tree.
   * Recursively traverses the entire tree and gathers tiles where selected=true.
   *
   * @param result - Accumulator array for selected tiles
   * @returns Array of selected OSMNode tiles
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
   * Calculate the 3D bounding volume for this tile in deck.gl's common
   * coordinate space for frustum culling.
   *
   */
  getBoundingVolume(
    zRange: ZRange,
    project: ((xyz: number[]) => number[]) | null,
  ) {
    const overview = this.overview;
    const { bbox } = this.cogMetadata;

    const refPoints = REF_POINTS_9;

    // Sample points across the tile surface and project to common space
    const refPointPositions: number[][] = [];
    for (const [pX, pY] of refPoints) {
      // Convert tile-relative coordinates [0-1] to geographic coordinates in
      // the COG's CRS
    }

    // TODO: use tileWidth/tileHeight from cogMetadata instead?
    const cogWidth = bbox[2] - bbox[0];
    const cogHeight = bbox[3] - bbox[1];

    const tileGeoWidth = cogWidth / overview.tilesX;
    const tileGeoHeight = cogHeight / overview.tilesY;

    const tileMinX = bbox[0] + this.x * tileGeoWidth;
    const tileMinY = bbox[1] + this.y * tileGeoHeight;
    const tileMaxX = tileMinX + tileGeoWidth;
    const tileMaxY = tileMinY + tileGeoHeight;

    console.log("Tile bounding box:");
    console.log(tileMinX, tileMinY, tileMaxX, tileMaxY);

    if (project) {
      assert(false, "TODO: check bounding volume implementation in Globe view");

      // Custom projection (e.g., GlobeView)
      // Estimate bounding box from sample points
      // TODO: switch to higher ref points at lowest zoom levels, like upstream
      // const refPoints = REF_POINTS_5;

      // const refPointPositions: number[][] = [];
      // for (const [fx, fy] of refPoints) {
      //   const geoX = tileMinX + fx * tileGeoWidth;
      //   const geoY = tileMinY + fy * tileGeoHeight;

      //   // Convert from COG coordinates to lng/lat
      //   // This assumes COG is in Web Mercator - adjust for other projections
      //   const lngLat = this.cogCoordsToLngLat([geoX, geoY]);
      //   lngLat[2] = zRange[0];
      //   refPointPositions.push(project(lngLat));

      //   if (zRange[0] !== zRange[1]) {
      //     lngLat[2] = zRange[1];
      //     refPointPositions.push(project(lngLat));
      //   }
      // }

      // return makeOrientedBoundingBoxFromPoints(refPointPositions);
    }

    // Reproject tile bounds to Web Mercator for bounding volume
    const ll = this.cogMetadata.projectTo3857.forward([tileMinX, tileMinY]);
    const lr = this.cogMetadata.projectTo3857.forward([tileMaxX, tileMinY]);
    const ur = this.cogMetadata.projectTo3857.forward([tileMaxX, tileMaxY]);
    const ul = this.cogMetadata.projectTo3857.forward([tileMinX, tileMaxY]);

    const webMercatorMinX = Math.min(ll[0], lr[0], ur[0], ul[0]);
    const webMercatorMaxX = Math.max(ll[0], lr[0], ur[0], ul[0]);
    const webMercatorMinY = Math.min(ll[1], lr[1], ur[1], ul[1]);
    const webMercatorMaxY = Math.max(ll[1], lr[1], ur[1], ul[1]);

    console.log("Tile Web Mercator bounds:");
    console.log(
      webMercatorMinX,
      webMercatorMinY,
      webMercatorMaxX,
      webMercatorMaxY,
    );

    // Web Mercator projection
    // Convert from Web Mercator meters to deck.gl's common space (world units)
    // Web Mercator range: [-20037508.34, 20037508.34] meters
    // deck.gl world space: [0, 512]
    const WORLD_SIZE = 512; // deck.gl's world size
    const WEB_MERCATOR_MAX = 20037508.342789244; // Half Earth circumference

    // Offset from [-20M, 20M] to [0, 40M], then normalize to [0, 512]
    const worldMinX =
      ((webMercatorMinX + WEB_MERCATOR_MAX) / (2 * WEB_MERCATOR_MAX)) *
      WORLD_SIZE;
    const worldMaxX =
      ((webMercatorMaxX + WEB_MERCATOR_MAX) / (2 * WEB_MERCATOR_MAX)) *
      WORLD_SIZE;

    // Y is flipped in deck.gl's common space
    const worldMinY =
      WORLD_SIZE -
      ((webMercatorMaxY + WEB_MERCATOR_MAX) / (2 * WEB_MERCATOR_MAX)) *
        WORLD_SIZE;
    const worldMaxY =
      WORLD_SIZE -
      ((webMercatorMinY + WEB_MERCATOR_MAX) / (2 * WEB_MERCATOR_MAX)) *
        WORLD_SIZE;

    console.log("Tile world X bounds:");
    console.log("Tile world bounds:");
    console.log(worldMinX, worldMinY, worldMaxX, worldMaxY);

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
    const [lng, lat] = this.cogMetadata.projectToWgs84.forward([x, y]);
    return [lng, lat, 0];
  }
}

/**
 * Get tile indices visible in viewport
 * Uses frustum culling similar to OSM implementation
 *
 * Overviews follow TileMatrixSet ordering: index 0 = coarsest, higher = finer
 */
export function getTileIndices(
  cogMetadata: COGMetadata,
  opts: {
    viewport: Viewport;
    maxZ?: number;
    // minZ?: number;
    zRange: ZRange | null;
  },
): COGTileIndex[] {
  const { viewport, maxZ, zRange } = opts;

  // console.log("=== getTileIndices called ===");
  // console.log("Viewport:", viewport);
  // console.log("maxZ:", maxZ);
  // console.log("COG metadata overviews count:", cogMetadata.overviews.length);
  // console.log("COG bbox:", cogMetadata.bbox);

  const project: ((xyz: number[]) => number[]) | null =
    viewport instanceof _GlobeViewport && viewport.resolution
      ? viewport.projectPosition
      : null;

  // Get the culling volume of the current camera
  const planes: Plane[] = Object.values(viewport.getFrustumPlanes()).map(
    ({ normal, distance }) => new Plane(normal.clone().negate(), distance),
  );
  const cullingVolume = new CullingVolume(planes);

  // Project zRange from meters to common space
  const unitsPerMeter = viewport.distanceScales.unitsPerMeter[2];
  const elevationMin = (zRange && zRange[0] * unitsPerMeter) || 0;
  const elevationMax = (zRange && zRange[1] * unitsPerMeter) || 0;

  // // Always load at the current zoom level if pitch is small
  // const minZ =
  //   viewport instanceof WebMercatorViewport && viewport.pitch <= 60 ? maxZ : 0;

  // // Map maxZoom/minZoom to COG overview levels
  // // In COG: level 0 = full resolution (finest), higher levels = coarser
  // // In deck.gl zoom: higher = finer
  // // So we need to invert: maxZoom (finest) → minLevel (level 0)
  // const minLevel = 0; // Always allow full resolution
  // const maxLevel = Math.min(
  //   cogMetadata.overviews.length - 1,
  //   Math.max(0, cogMetadata.overviews.length - 1 - (maxZ || 0)),
  // );

  // Start from coarsest overview
  const coarsestOverview = cogMetadata.overviews[0];

  // Create root tiles at coarsest level
  // In contrary to OSM tiling, we usually have more than one tile at the
  // coarsest level (z=0)
  const roots: COGTileNode[] = [];
  for (let y = 0; y < coarsestOverview.tilesY; y++) {
    for (let x = 0; x < coarsestOverview.tilesX; x++) {
      roots.push(new COGTileNode(x, y, 0, cogMetadata));
    }
  }

  // Traverse and update visibility
  const traversalParams = {
    viewport,
    project,
    cullingVolume,
    elevationBounds: [elevationMin, elevationMax] as ZRange,
    minZ: 0,
    maxZ,
  };
  console.log("Traversal params:", traversalParams);

  for (const root of roots) {
    root.update(traversalParams);
  }
  console.log("roots", roots);

  // Collect selected tiles
  const selectedNodes: COGTileNode[] = [];
  for (const root of roots) {
    root.getSelected(selectedNodes);
  }

  return selectedNodes;
}

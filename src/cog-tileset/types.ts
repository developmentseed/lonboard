import type { GeoTIFF } from "geotiff";

export type ZRange = [minZ: number, maxZ: number];

export type Bounds = [minX: number, minY: number, maxX: number, maxY: number];

export type GeoBoundingBox = {
  west: number;
  north: number;
  east: number;
  south: number;
};
export type NonGeoBoundingBox = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};

export type TileBoundingBox = NonGeoBoundingBox | GeoBoundingBox;

export type TileIndex = { x: number; y: number; z: number };

export type TileLoadProps = {
  index: TileIndex;
  id: string;
  bbox: TileBoundingBox;
  url?: string | null;
  signal?: AbortSignal;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  userData?: Record<string, any>;
  zoom?: number;
};

////////////////
// Claude-generated metadata
////////////////

/**
 * Represents a single resolution level in a Cloud Optimized GeoTIFF.
 *
 * COGs contain multiple resolution levels (overviews) for efficient
 * visualization at different zoom levels.
 *
 * IMPORTANT: Overviews are ordered according to TileMatrixSet specification:
 * - Index 0: Coarsest resolution (most zoomed out)
 * - Index N: Finest resolution (most zoomed in)
 *
 * This matches the natural ordering where z increases with detail.
 */
export type COGOverview = {
  /**
   * Overview index in the TileMatrixSet ordering.
   * - Index 0: Coarsest resolution (most zoomed out)
   * - Higher indices: Progressively finer resolution
   *
   * This is the index in the COGMetadata.overviews array and represents
   * the natural ordering from coarse to fine.
   *
   * Note: This is different from GeoTIFF's internal level numbering where
   * level 0 is the full resolution image.
   *
   * @example
   * // For a COG with 4 resolutions:
   * index: 0  // Coarsest:  1250x1000 pixels (8x downsampled)
   * index: 1  // Medium:    2500x2000 pixels (4x downsampled)
   * index: 2  // Fine:      5000x4000 pixels (2x downsampled)
   * index: 3  // Finest:   10000x8000 pixels (full resolution)
   */
  level: number;

  /**
   * Zoom index (OSM convention).
   * Defined as: maxLevel - currentLevel
   *
   * This makes the code compatible with OSM tile indexing where:
   * - Higher z = finer detail (opposite of COG level)
   * - Lower z = coarser detail
   *
   * In TileMatrixSet ordering: z === level (both increase with detail)
   */
  z: number;

  /**
   * Width of the entire image at this overview level, in pixels.
   */
  width: number;
  /**
   * Height of the entire image at this overview level, in pixels.
   */
  height: number;

  /**
   * Number of tiles in the X (horizontal) direction at this overview level.
   *
   * Calculated as: Math.ceil(width / tileWidth)
   *
   * @example
   * // If tileWidth = 512:
   * tilesX: 3   // z=0: ceil(1250 / 512)
   * tilesX: 5   // z=1: ceil(2500 / 512)
   * tilesX: 10  // z=2: ceil(5000 / 512)
   * tilesX: 20  // z=3: ceil(10000 / 512)
   */
  tilesX: number;

  /**
   * Number of tiles in the Y (vertical) direction at this overview level.
   *
   * Calculated as: Math.ceil(height / tileHeight)
   *
   * @example
   * // If tileHeight = 512:
   * tilesY: 2   // z=0: ceil(1000 / 512)
   * tilesY: 4   // z=1: ceil(2000 / 512)
   * tilesY: 8   // z=2: ceil(4000 / 512)
   * tilesY: 16  // z=3: ceil(8000 / 512)
   */
  tilesY: number;

  /**
   * Downsampling scale factor relative to full resolution (finest level).
   *
   * Indicates how much this overview is downsampled compared to the finest resolution.
   * - Scale factor of 1: Full resolution (finest level)
   * - Scale factor of 2: Half resolution
   * - Scale factor of 4: Quarter resolution
   * - Scale factor of 8: Eighth resolution (coarsest in this example)
   *
   * Common pattern: Each overview is 2x downsampled from the next finer level,
   * so scale factors are powers of 2: 8, 4, 2, 1 (from coarsest to finest)
   *
   * @example
   * scaleFactor: 8   // z=0: 1250x1000  (8x downsampled from finest)
   * scaleFactor: 4   // z=1: 2500x2000  (4x downsampled)
   * scaleFactor: 2   // z=2: 5000x4000  (2x downsampled)
   * scaleFactor: 1   // z=3: 10000x8000 (full resolution)
   */
  scaleFactor: number;

  /**
   * Index in the original GeoTIFF file.
   *
   * GeoTIFF stores: image 0 = full resolution, image 1+ = overviews (progressively coarser)
   * This index is needed to read the correct image from the GeoTIFF file.
   *
   * Note: This may differ from `level` since we reorder overviews to TileMatrixSet order.
   *
   * @example
   * // TileMatrixSet order (our array):
   * level: 0, geoTiffIndex: 3  // Coarsest (GeoTIFF overview 3)
   * level: 1, geoTiffIndex: 2  // Medium (GeoTIFF overview 2)
   * level: 2, geoTiffIndex: 1  // Fine (GeoTIFF overview 1)
   * level: 3, geoTiffIndex: 0  // Finest (GeoTIFF main image)
   */
  geoTiffIndex: number;
};

/**
 * COG Metadata extracted from GeoTIFF
 */
export type COGMetadata = {
  width: number;
  height: number;
  tileWidth: number;
  tileHeight: number;
  tilesX: number;
  tilesY: number;
  bbox: Bounds; // COG's CRS
  projection: string | null;
  overviews: COGOverview[];
  image: GeoTIFF; // GeoTIFF reference
};

/**
 * COG Tile Index
 *
 * In TileMatrixSet ordering: level === z (both 0 = coarsest, higher = finer)
 */
export type COGTileIndex = {
  x: number;
  y: number;
  z: number; // TileMatrixSet/OSM zoom (0 = coarsest, higher = finer)
  level: number; // Same as z in TileMatrixSet ordering
  geoTiffIndex?: number; // Index in GeoTIFF file (for reading tiles)
  bounds?: Bounds;
};

////////////////
// TileMatrixSet
////////////////

// type CRS = string | { [k: string]: unknown };
export type TMSCrs = unknown;

/**
 * A 2D Point in the CRS indicated elsewhere
 *
 * @minItems 2
 * @maxItems 2
 */
export type TMSPoint = [number, number];

/**
 * Minimum bounding rectangle surrounding a 2D resource in the CRS indicated elsewhere
 */
export interface TMSBoundingBox {
  lowerLeft: TMSPoint;
  upperRight: TMSPoint;
  crs?: TMSCrs;
  /**
   * @minItems 2
   * @maxItems 2
   */
  orderedAxes?: [string, string];
  [k: string]: unknown;
}

/**
 * A definition of a tile matrix set following the Tile Matrix Set standard. For tileset metadata, such a description (in `tileMatrixSet` property) is only required for offline use, as an alternative to a link with a `http://www.opengis.net/def/rel/ogc/1.0/tiling-scheme` relation type.
 */
export type TileMatrixSetDefinition = {
  /**
   * Title of this tile matrix set, normally used for display to a human
   */
  title?: string;
  /**
   * Brief narrative description of this tile matrix set, normally available for display to a human
   */
  description?: string;
  /**
   * Unordered list of one or more commonly used or formalized word(s) or phrase(s) used to describe this tile matrix set
   */
  keywords?: string[];
  /**
   * Tile matrix set identifier. Implementation of 'identifier'
   */
  id?: string;
  /**
   * Reference to an official source for this tileMatrixSet
   */
  uri?: string;
  /**
   * @minItems 1
   */
  orderedAxes?: [string, ...string[]];
  crs: TMSCrs;
  /**
   * Reference to a well-known scale set
   */
  wellKnownScaleSet?: string;
  boundingBox?: {
    [k: string]: unknown;
  } & TMSBoundingBox;
  /**
   * Describes scale levels and its tile matrices
   */
  tileMatrices: TMSTileMatrix[];
  [k: string]: unknown;
};

/**
 * A tile matrix, usually corresponding to a particular zoom level of a TileMatrixSet.
 */
export interface TMSTileMatrix {
  /**
   * Title of this tile matrix, normally used for display to a human
   */
  title?: string;
  /**
   * Brief narrative description of this tile matrix set, normally available for display to a human
   */
  description?: string;
  /**
   * Unordered list of one or more commonly used or formalized word(s) or phrase(s) used to describe this dataset
   */
  keywords?: string[];
  /**
   * Identifier selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile. Implementation of 'identifier'
   */
  id: string;
  /**
   * Scale denominator of this tile matrix
   */
  scaleDenominator: number;
  /**
   * Cell size of this tile matrix
   */
  cellSize: number;
  /**
   * The corner of the tile matrix (_topLeft_ or _bottomLeft_) used as the origin for numbering tile rows and columns. This corner is also a corner of the (0, 0) tile.
   */
  cornerOfOrigin?: "topLeft" | "bottomLeft";
  pointOfOrigin: {
    [k: string]: unknown;
  } & TMSPoint;
  /**
   * Width of each tile of this tile matrix in pixels
   */
  tileWidth: number;
  /**
   * Height of each tile of this tile matrix in pixels
   */
  tileHeight: number;
  /**
   * Width of the matrix (number of tiles in width)
   */
  matrixHeight: number;
  /**
   * Height of the matrix (number of tiles in height)
   */
  matrixWidth: number;
  /**
   * Describes the rows that has variable matrix width
   */
  variableMatrixWidths?: object[];
  [k: string]: unknown;
}

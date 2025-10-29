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

/**
 * Custom tile index for COG tiles
 */
export type COGTileIndex = TileIndex & {
  // Optional: include bounds for debugging/rendering
  bounds?: [number, number, number, number];
};

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

/**
 * @fileoverview Type definitions for DeckGL structures used in e2e tests.
 *
 * These types describe the runtime DeckGL objects accessed via window.__deck.
 * They are not exhaustive - only the properties we use in tests are typed.
 */

/**
 * Geographic coordinate [longitude, latitude]
 */
export type Coordinate = [number, number];

/**
 * Pixel coordinate [x, y]
 */
export type PixelCoordinate = [number, number];

/**
 * Information about what was picked at a given screen coordinate.
 * Returned by deck.pickObject() and passed to event handlers.
 */
export interface PickingInfo {
  x: number;
  y: number;
  object: unknown | null;
  layer: unknown | null;
  index: number;
  coordinate?: Coordinate;
  pixel?: PixelCoordinate;
}

/**
 * DeckGL viewport for coordinate projection/unprojection
 */
export interface Viewport {
  unproject?: (pixelCoords: PixelCoordinate) => Coordinate;
}

/**
 * DeckGL event handlers
 */
export interface DeckGLProps {
  onClick?: (info: PickingInfo, event: DeckGLEvent) => void;
  onHover?: (info: PickingInfo, event: DeckGLEvent) => void;
  onDragStart?: (event: DeckGLEvent) => void;
  onDrag?: (event: DeckGLEvent) => void;
  onDragEnd?: (event: DeckGLEvent) => void;
}

/**
 * DeckGL event payload passed to handlers
 */
export interface DeckGLEvent {
  type: string;
  srcEvent: PointerEvent;
  center: PixelCoordinate;
  offsetCenter: { x: number; y: number };
}

/**
 * The DeckGL instance exposed on window for testing
 */
export interface DeckGLInstance {
  pickObject?: (options: {
    x: number;
    y: number;
    radius?: number;
  }) => PickingInfo | undefined;
  getViewports?: () => Viewport[] | undefined;
  props: DeckGLProps;
}

/**
 * Window with DeckGL instance attached for testing
 */
export interface WindowWithDeck extends Window {
  __deck: DeckGLInstance;
}

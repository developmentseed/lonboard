import type { Page } from "@playwright/test";
import type {
  PickingInfo,
  DeckGLInstance,
  WindowWithDeck,
  Coordinate,
  DeckGLEvent,
} from "./types";

/**
 * @fileoverview DeckGL canvas interaction helpers for Playwright e2e tests.
 *
 * These helpers work by accessing the DeckGL instance via `window.__deck`, which is
 * exposed in src/index.tsx:100 for testing purposes. This allows tests to directly
 * invoke DeckGL's event handlers (onClick, onHover, etc.) with properly constructed
 * event payloads, bypassing Playwright's DOM event system which doesn't reliably
 * trigger DeckGL's event pipeline.
 *
 * All coordinate parameters use canvas-relative pixel coordinates (offsets from the
 * canvas element's top-left corner), NOT page-relative coordinates.
 *
 * ## Common patterns used in browser context (inside page.evaluate):
 *
 * 1. **Access DeckGL instance:**
 *    ```ts
 *    const deck = (window as any).__deck;
 *    if (!deck) throw new Error("No deck instance on window");
 *    ```
 *
 * 2. **Unproject pixel coordinates to geographic coordinates:**
 *    ```ts
 *    const coordinate = (() => {
 *      if (info?.coordinate) return info.coordinate;
 *      try {
 *        const viewport = deck.getViewports()?.[0];
 *        return viewport?.unproject?.([x, y]);
 *      } catch (e) {
 *        console.error("Failed to unproject coordinates:", e);
 *      }
 *    })();
 *    ```
 */

/**
 * Simulates pointer interactions on the DeckGL canvas at the specified coordinates.
 *
 * @param page - Playwright page object
 * @param action - Type of pointer event: "click" or "hover"
 * @param x - X coordinate in canvas-relative pixels (offset from canvas left edge)
 * @param y - Y coordinate in canvas-relative pixels (offset from canvas top edge)
 *
 * @remarks
 * Coordinates are canvas-relative, meaning they are pixel offsets from the top-left
 * corner of the canvas element itself, NOT from the page. Even if the canvas is
 * scrolled or positioned elsewhere in the page, always use canvas-relative coordinates.
 *
 * The function works by:
 * 1. Using DeckGL's pickObject() to get object info at the position
 * 2. Converting pixel coordinates to geographic coordinates via viewport.unproject()
 * 3. Building a proper PickingInfo object with coordinate data
 * 4. Invoking the appropriate DeckGL event handler (onClick or onHover)
 *
 * This approach bypasses the DOM event system entirely and works directly with
 * DeckGL's event handlers, which is necessary because Playwright's mouse events
 * don't reliably trigger DeckGL's event pipeline.
 *
 * @example
 * ```typescript
 * // Simulate a click
 * await deckPointerEvent(page, "click", 200, 300);
 *
 * // Simulate a hover
 * await deckPointerEvent(page, "hover", 400, 500);
 * ```
 */
export async function deckPointerEvent(
  page: Page,
  action: "click" | "hover",
  x: number,
  y: number,
): Promise<void> {
  await page.evaluate(
    (args) => {
      const { action, x, y } = args;
      const win = window as unknown as WindowWithDeck;
      const deck: DeckGLInstance = win.__deck;

      if (!deck) {
        throw new Error("No deck instance on window");
      }

      let info: PickingInfo | undefined = deck.pickObject?.({
        x,
        y,
        radius: 2,
      });

      const coordinate: Coordinate | undefined = (() => {
        if (info?.coordinate) return info.coordinate;
        try {
          const viewport = deck.getViewports?.()?.[0];
          return viewport?.unproject?.([x, y]);
        } catch (e) {
          console.error("Failed to unproject coordinates:", e);
          return undefined;
        }
      })();

      if (!info) {
        info = {
          x,
          y,
          object: null,
          layer: null,
          index: -1,
          coordinate: action === "click" ? coordinate || [0, 0] : coordinate,
          ...(action === "click" ? { pixel: [x, y] as [number, number] } : {}),
        };
      } else if (!info.coordinate && coordinate) {
        info.coordinate = coordinate;
      }

      const isClick = action === "click";
      const type = isClick ? "click" : "pointermove";
      const buttons = isClick ? 1 : 0;
      const srcEvent = new PointerEvent(type, {
        clientX: x,
        clientY: y,
        buttons,
        pointerType: "mouse",
        bubbles: true,
      });
      const evt: DeckGLEvent = {
        type,
        srcEvent,
        center: [x, y],
        offsetCenter: { x, y },
      };

      if (isClick) {
        deck.props.onClick?.(info, evt);
      } else {
        deck.props.onHover?.(info, evt);
      }
    },
    { action, x, y },
  );
}

export async function deckDrag(
  page: Page,
  start: { x: number; y: number },
  end: { x: number; y: number },
  steps: number = 5,
) {
  await page.evaluate(
    (args) => {
      const { start, end, steps } = args;
      const win = window as unknown as WindowWithDeck;
      const deck: DeckGLInstance = win.__deck;

      if (!deck) {
        throw new Error("No deck instance on window");
      }

      const makeEvent = (
        type: string,
        x: number,
        y: number,
        buttons: number,
      ): DeckGLEvent => {
        const srcEvent = new PointerEvent(type, {
          clientX: x,
          clientY: y,
          buttons,
          pointerType: "mouse",
          bubbles: true,
        });
        return {
          type,
          srcEvent,
          center: [x, y],
          offsetCenter: { x, y },
        };
      };

      if (deck.props.onDragStart) {
        deck.props.onDragStart(makeEvent("pointerdown", start.x, start.y, 1));
      }

      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const x = start.x + (end.x - start.x) * t;
        const y = start.y + (end.y - start.y) * t;

        if (deck.props.onDrag) {
          deck.props.onDrag(makeEvent("pointermove", x, y, 1));
        }
      }

      if (deck.props.onDragEnd) {
        deck.props.onDragEnd(makeEvent("pointerup", end.x, end.y, 0));
      }
    },
    { start, end, steps },
  );
}

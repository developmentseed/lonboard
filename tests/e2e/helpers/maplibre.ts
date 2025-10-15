import type { Page } from "@playwright/test";

/**
 * Draws a bounding box on the MapLibre map using click-click pattern.
 * In overlay mode, MapLibre handles events and forwards them to deck.gl via MapboxOverlay.
 *
 * The bbox selection pattern matches deck-first mode: click at start, hover at end, click at end.
 */
export async function drawBboxOnMapLibre(
  page: Page,
  start: { x: number; y: number },
  end: { x: number; y: number },
): Promise<void> {
  // Find the map canvas (MapLibre renders the map canvas directly)
  const canvas = page.locator("canvas").first();
  await canvas.waitFor({ state: "visible", timeout: 10000 });

  // Bbox selection pattern: click at start, hover at end, click at end
  // Use locator-based actions which are more robust than page.mouse
  await canvas.click({ position: { x: start.x, y: start.y } });
  await page.waitForTimeout(500);

  await canvas.hover({ position: { x: end.x, y: end.y } });
  await page.waitForTimeout(500);

  await canvas.click({ position: { x: end.x, y: end.y } });
  await page.waitForTimeout(1000);
}

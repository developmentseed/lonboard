import { test, expect, Page } from "@playwright/test";
import { deckPointerEvent } from "./helpers/deckgl";
import {
  openNotebook,
  runCells,
  waitForMapReady,
  executeCellAndWaitForOutput,
} from "./helpers/notebook";
import { validateBounds } from "./helpers/assertions";

/**
 * Draws a bounding box on the DeckGL canvas by clicking start and end positions.
 */
async function drawBbox(
  page: Page,
  start: { x: number; y: number },
  end: { x: number; y: number },
) {
  // Click to set bbox start position
  await deckPointerEvent(page, "click", start.x, start.y);
  await page.waitForTimeout(300);

  // Hover to preview bbox size
  await deckPointerEvent(page, "hover", end.x, end.y);
  await page.waitForTimeout(300);

  // Click to set bbox end position and complete drawing
  await deckPointerEvent(page, "click", end.x, end.y);
  await page.waitForTimeout(500);
}

test.describe("BBox selection", () => {
  test("draws bbox and syncs selected_bounds to Python", async ({ page }) => {
    const notebook = await openNotebook(page, "simple-map.ipynb");
    await runCells(notebook, 0, 2);
    await waitForMapReady(page);
    await page.waitForTimeout(2000);

    // Start bbox selection mode
    const bboxButton = page.getByRole("button", { name: "Select BBox" });
    await expect(bboxButton).toBeVisible({ timeout: 10000 });
    await bboxButton.click();

    // Verify drawing mode is active
    const cancelButton = page.getByRole("button", { name: "Cancel drawing" });
    await expect(cancelButton).toBeVisible({ timeout: 5000 });

    // Draw bbox using canvas-relative coordinates (pixels from canvas top-left)
    await drawBbox(page, { x: 200, y: 200 }, { x: 400, y: 400 });

    // Verify bbox was drawn
    const clearButton = page.getByRole("button", {
      name: "Clear bounding box",
    });
    await expect(clearButton).toBeVisible({ timeout: 2000 });

    // Execute cell to check selected bounds
    const output = await executeCellAndWaitForOutput(notebook, 2);

    // Verify bounds are valid geographic coordinates
    const outputText = await output.textContent();
    validateBounds(outputText);
  });
});

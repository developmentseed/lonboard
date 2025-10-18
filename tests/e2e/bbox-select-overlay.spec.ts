import { test, expect } from "@playwright/test";
import {
  openNotebookFresh,
  runFirstNCells,
  executeCellAndWaitForOutput,
} from "./helpers/notebook";
import { validateBounds } from "./helpers/assertions";
import { drawBboxOnMapLibre } from "./helpers/maplibre";

test.describe("BBox selection - Overlay render mode", () => {
  test("draws bbox and syncs selected_bounds to Python with overlay render_mode", async ({
    page,
  }) => {
    const { notebookRoot } = await openNotebookFresh(
      page,
      "simple-map-overlay.ipynb",
      {
        workspaceId: `bbox-overlay-${Date.now()}`,
      },
    );
    await runFirstNCells(page, notebookRoot, 2);
    await page.waitForTimeout(5000);

    // Start bbox selection mode
    const bboxButton = page.getByRole("button", { name: "Select BBox" });
    await expect(bboxButton).toBeVisible({ timeout: 10000 });
    await bboxButton.click();

    // Verify drawing mode is active
    const cancelButton = page.getByRole("button", { name: "Cancel drawing" });
    await expect(cancelButton).toBeVisible({ timeout: 5000 });

    // Draw bbox using simple mouse events
    await drawBboxOnMapLibre(page, { x: 200, y: 200 }, { x: 400, y: 400 });

    // Verify bbox was drawn successfully
    const finalClearButton = page.getByRole("button", {
      name: "Clear bounding box",
    });
    await expect(finalClearButton).toBeVisible({ timeout: 5000 });

    // Execute cell to check selected bounds
    const output = await executeCellAndWaitForOutput(notebookRoot, 2);
    const outputText = await output.textContent();
    validateBounds(outputText);
  });
});

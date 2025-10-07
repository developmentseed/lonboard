import { test, expect } from "@playwright/test";
import {
  openNotebookFresh,
  runFirstNCells,
  ignoreKnownWidgetNoise,
} from "./helpers/notebook";

/** Globe projection e2e checks (minimal). */

test.describe("Globe View", () => {
  // TODO: Fix test isolation - these tests fail when multiple notebooks are open
  // The test environment needs to ensure a clean JupyterLab state between tests

  test("renders map with globe projection", async ({ page }) => {
    ignoreKnownWidgetNoise(page);

    // Open the notebook in a fresh workspace and focus it deterministically
    const { notebookRoot } = await openNotebookFresh(page, "globe-view.ipynb", {
      workspaceId: `globe-${Date.now()}`,
    });

    // Run first two cells
    await runFirstNCells(page, notebookRoot, 2);

    // Wait for globe container
    const globeContainer = page.locator("#globe-map").first();
    await expect(globeContainer).toBeVisible({ timeout: 30000 });

    // Ensure globe container has rendered dimensions
    await expect
      .poll(
        async () => {
          const box = await globeContainer.boundingBox();
          return box && box.width > 0 && box.height > 0;
        },
        { timeout: 10000 },
      )
      .toBe(true);

    // Poll until MapLibre reports globe projection
    await expect
      .poll(
        async () => {
          return await page.evaluate(() => {
            const container = document.querySelector("#globe-map") as
              | (HTMLElement & {
                  _map?: { getProjection?: () => { type: string } };
                })
              | null;
            if (!container) return null;
            const map = container._map;
            if (!map || !map.getProjection) return null;
            return map.getProjection().type;
          });
        },
        { timeout: 10000 },
      )
      .toBe("globe");
  });

  test("layers render on globe canvas", async ({ page }) => {
    const { notebookRoot } = await openNotebookFresh(page, "globe-view.ipynb");
    await runFirstNCells(page, notebookRoot, 2);

    // Use MapLibre canvas (MapboxOverlay path) to verify rendering
    const mlCanvas = page.locator("canvas.maplibregl-canvas").first();
    await expect(mlCanvas).toBeVisible({ timeout: 30000 });
    const mlBox = await mlCanvas.boundingBox();
    expect(mlBox).toBeTruthy();
    expect(mlBox!.width).toBeGreaterThan(0);
    expect(mlBox!.height).toBeGreaterThan(0);
  });
});

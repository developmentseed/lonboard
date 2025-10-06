import { test, expect } from "@playwright/test";
import { deckClick, deckHover } from "./helpers/deck-interaction";
import { openNotebook, runCells, waitForMapReady } from "./helpers/notebook";

test.describe("BBox selection", () => {
  test("draws bbox and syncs selected_bounds to Python", async ({ page }) => {
    const notebook = await openNotebook(page, "simple-map.ipynb");
    await runCells(notebook, 0, 2);
    await waitForMapReady(page);
    await page.waitForTimeout(2000);

    const bboxButton = page.getByRole("button", { name: "Select BBox" });
    await expect(bboxButton).toBeVisible({ timeout: 10000 });
    await bboxButton.click();

    const cancelButton = page.getByRole("button", { name: "Cancel drawing" });
    await expect(cancelButton).toBeVisible({ timeout: 5000 });

    const deckCanvas = page.locator('canvas#deckgl-overlay').first();
    const canvasBox = await deckCanvas.boundingBox();
    if (!canvasBox) throw new Error("Canvas not found");

    const startX = canvasBox.x + 200;
    const startY = canvasBox.y + 200;
    const endX = canvasBox.x + 400;
    const endY = canvasBox.y + 400;

    await deckClick(page, startX, startY);
    await page.waitForTimeout(300);
    await deckHover(page, endX, endY);
    await page.waitForTimeout(300);
    await deckClick(page, endX, endY);
    await page.waitForTimeout(500);

    const clearButton = page.getByRole("button", { name: "Clear bounding box" });
    await expect(clearButton).toBeVisible({ timeout: 2000 });

    await notebook.locator(".jp-Cell").nth(2).click();
    await page.keyboard.press("Shift+Enter");

    const output = page.locator(".jp-OutputArea-output").last();
    await expect(output).toBeVisible({ timeout: 5000 });
    await expect(output).toContainText(/Selected bounds: \([-\d\., ]+\)/);
  });
});

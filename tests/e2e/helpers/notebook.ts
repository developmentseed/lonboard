import { expect, type Page, type Locator } from "@playwright/test";
import { waitForDeck } from "./deck-interaction";
export async function openNotebook(page: Page, notebookPath: string): Promise<Locator> {
  await page.goto(`/lab/tree/${notebookPath}`);
  const notebook = page.locator(".jp-Notebook");
  await expect(notebook).toBeVisible({ timeout: 30000 });
  return notebook;
}

export async function runCell(notebook: Locator, cellIndex: number): Promise<void> {
  await notebook.locator(".jp-Cell").nth(cellIndex).click();
  await notebook.page().keyboard.press("Shift+Enter");
}

export async function runCells(notebook: Locator, startIndex: number, count: number): Promise<void> {
  await notebook.locator(".jp-Cell").nth(startIndex).click();
  for (let i = 0; i < count; i++) {
    await notebook.page().keyboard.press("Shift+Enter");
  }
}

export async function waitForMapReady(page: Page): Promise<void> {
  const mapRoot = page.locator("[data-jp-suppress-context-menu]");
  await expect(mapRoot.first()).toBeVisible({ timeout: 30000 });

  const deckCanvas = page.locator('[id^="map-"] canvas#deckgl-overlay').first();
  await expect(deckCanvas).toBeVisible({ timeout: 30000 });

  await expect
    .poll(async () => {
      const box = await deckCanvas.boundingBox();
      return box && box.width > 0 && box.height > 0;
    }, { timeout: 10000 })
    .toBe(true);

  await waitForDeck(page);
}

export function getCellOutput(notebook: Locator, cellIndex: number): Locator {
  return notebook.locator(".jp-Cell").nth(cellIndex).locator(".jp-OutputArea-output").last();
}

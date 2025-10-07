/**
 * @fileoverview JupyterLab notebook helpers for Playwright e2e tests.
 *
 * These helpers provide utilities for interacting with JupyterLab notebooks,
 * including opening notebooks, executing cells, and waiting for map widgets
 * to be ready for interaction.
 */

import { expect, type Page, type Locator } from "@playwright/test";
import type { WindowWithDeck } from "./deckgl";

/**
 * Opens a notebook in JupyterLab and waits for it to be visible.
 *
 * @param page - Playwright page object
 * @param notebookPath - Path to the notebook relative to JupyterLab root
 * @returns Locator for the notebook element
 *
 * @example
 * ```typescript
 * const notebook = await openNotebook(page, "simple-map.ipynb");
 * ```
 */
export async function openNotebook(
  page: Page,
  notebookPath: string,
): Promise<Locator> {
  await page.goto(`/lab/tree/${notebookPath}`);
  const notebook = page.locator(".jp-Notebook");
  await expect(notebook).toBeVisible({ timeout: 30000 });
  return notebook;
}

/**
 * Executes a single notebook cell by clicking it and pressing Shift+Enter.
 *
 * @param notebook - The notebook locator
 * @param cellIndex - Zero-based index of the cell to execute
 *
 * @example
 * ```typescript
 * await runCell(notebook, 0); // Run first cell
 * ```
 */
export async function runCell(
  notebook: Locator,
  cellIndex: number,
): Promise<void> {
  await notebook.locator(".jp-Cell").nth(cellIndex).click();
  await notebook.page().keyboard.press("Shift+Enter");
}

/**
 * Executes multiple consecutive notebook cells starting from a given index.
 *
 * @param notebook - The notebook locator
 * @param startIndex - Zero-based index of the first cell to execute
 * @param count - Number of cells to execute
 *
 * @example
 * ```typescript
 * await runCells(notebook, 0, 3); // Run cells 0, 1, and 2
 * ```
 */
export async function runCells(
  notebook: Locator,
  startIndex: number,
  count: number,
): Promise<void> {
  await notebook.locator(".jp-Cell").nth(startIndex).click();
  for (let i = 0; i < count; i++) {
    await notebook.page().keyboard.press("Shift+Enter");
  }
}

/**
 * Waits for the DeckGL instance to be available on the window object.
 *
 * @param page - Playwright page object
 * @param timeout - Maximum time to wait in milliseconds (default: 10000)
 */
export async function waitForDeck(
  page: Page,
  timeout: number = 10000,
): Promise<void> {
  await page.waitForFunction(
    () => {
      const win = window as unknown as WindowWithDeck;
      return typeof win.__deck !== "undefined";
    },
    { timeout },
  );
}

/**
 * Waits for a Lonboard map widget to be fully ready for interaction.
 *
 * @param page - Playwright page object
 *
 * @remarks
 * This function performs multiple checks to ensure the map is ready:
 * 1. Waits for the map root element with context menu suppression
 * 2. Waits for the DeckGL canvas overlay to be visible
 * 3. Polls until the canvas has non-zero dimensions
 * 4. Waits for the DeckGL instance to be available on window.__deck
 *
 * @example
 * ```typescript
 * await runCells(notebook, 0, 2);
 * await waitForMapReady(page);
 * // Now safe to interact with the map
 * ```
 */
export async function waitForMapReady(page: Page): Promise<void> {
  const mapRoot = page.locator("[data-jp-suppress-context-menu]");
  await expect(mapRoot.first()).toBeVisible({ timeout: 30000 });

  const deckCanvas = page.locator('[id^="map-"] canvas#deckgl-overlay').first();
  await expect(deckCanvas).toBeVisible({ timeout: 30000 });

  await expect
    .poll(
      async () => {
        const box = await deckCanvas.boundingBox();
        return box && box.width > 0 && box.height > 0;
      },
      { timeout: 10000 },
    )
    .toBe(true);

  await waitForDeck(page);
}

/**
 * Gets the output area locator for a specific notebook cell.
 *
 * @param notebook - The notebook locator
 * @param cellIndex - Zero-based index of the cell
 * @returns Locator for the cell's last output area
 *
 * @example
 * ```typescript
 * const output = getCellOutput(notebook, 2);
 * const text = await output.textContent();
 * ```
 */
export function getCellOutput(notebook: Locator, cellIndex: number): Locator {
  return notebook
    .locator(".jp-Cell")
    .nth(cellIndex)
    .locator(".jp-OutputArea-output")
    .last();
}

/**
 * Executes a notebook cell and waits for its output to appear.
 *
 * @param notebook - The notebook locator
 * @param cellIndex - Zero-based index of the cell to execute
 * @returns Locator for the cell's output area
 */
export async function executeCellAndWaitForOutput(
  notebook: Locator,
  cellIndex: number,
): Promise<Locator> {
  await notebook.locator(".jp-Cell").nth(cellIndex).click();
  await notebook.page().keyboard.press("Shift+Enter");

  // Wait for the cell to execute and produce output
  await notebook.page().waitForTimeout(1000);

  const output = notebook
    .locator(".jp-Cell")
    .nth(cellIndex)
    .locator(".jp-OutputArea-output")
    .first();
  await expect(output).toBeVisible({ timeout: 5000 });

  return output;
}

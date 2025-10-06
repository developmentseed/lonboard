import { test, expect } from '@playwright/test';

test.describe('Notebook Load', () => {
  test('JupyterLab starts and loads notebook', async ({ page }) => {
    // Open a simple map notebook
    await page.goto('/lab/tree/simple-map.ipynb');

    // Verify the correct notebook tab is active
    await expect(page.locator('.jp-mod-current[role="tab"]:has-text("simple-map.ipynb")')).toBeVisible({ timeout: 10000 });

    // Verify kernel status shows in footer
    await expect(page.locator('text=/Python 3.*Idle/')).toBeVisible({ timeout: 30000 });
  });
});

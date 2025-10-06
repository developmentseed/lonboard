import { test, expect } from '@playwright/test';
import { openNotebook } from './helpers/notebook';

test.describe('Notebook Load', () => {
  test('JupyterLab starts and loads notebook', async ({ page }) => {
    await openNotebook(page, 'simple-map.ipynb');

    await expect(page.locator('.jp-mod-current[role="tab"]:has-text("simple-map.ipynb")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/Python 3.*Idle/')).toBeVisible({ timeout: 30000 });
  });
});

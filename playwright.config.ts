import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60000,
  expect: {
    timeout: 30000,
  },
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:8889',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    navigationTimeout: 30000,
    browserName: 'chromium',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'uv run --group dev jupyter lab --no-browser --port=8889 --notebook-dir=tests/e2e/fixtures --IdentityProvider.token=""',
    url: 'http://localhost:8889',
    reuseExistingServer: false, // Always restart for clean state
    timeout: 30000,
  },
});

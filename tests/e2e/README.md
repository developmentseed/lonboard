# End-to-End Tests

Playwright-based end-to-end tests for Lonboard widgets in JupyterLab.

## Running Tests

```bash
# Run all e2e tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui
```

## Architecture

- **JupyterLab**: Runs on port 8889 (isolated from dev instances on 8888)
- **Working Directory**: `tests/e2e/fixtures/` (only test notebooks visible)
- **Clean State**: JupyterLab server restarts for each test run (`reuseExistingServer: false`)
  - Fresh kernel state on every run
  - No session persistence between test runs
  - No interference with development sessions

## Test Fixtures

Test notebooks are stored in `tests/e2e/fixtures/` and committed to the repository. They provide scaffolding to replicate correct user workflows.

### simple-map.ipynb

Basic test notebook with 4 points in a grid displaying a simple scatterplot map.

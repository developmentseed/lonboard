# End-to-End Tests

Playwright tests for Lonboard widgets in JupyterLab.

## Running Tests

```bash
npm run test:e2e        # Run all tests
npm run test:e2e:ui     # Run with UI mode
npm run jupyter:test    # Start test JupyterLab manually (port 8889)
```

## Architecture

- Tests run on port 8889 (isolated from dev on 8888)
- Fresh JupyterLab server per test run
- Fixtures in `tests/e2e/fixtures/`

## DeckGL Canvas Interactions

Playwright mouse events don't trigger DeckGL handlers. Use helpers from `helpers/deckgl/`:

```typescript
import { deckPointerEvent } from "./helpers/deckgl";

// Use canvas-relative coordinates (pixels from canvas top-left corner)
await deckPointerEvent(page, "click", 200, 300);
await deckPointerEvent(page, "hover", 400, 500);
```

The helpers automatically convert pixel coordinates to geographic coordinates and invoke DeckGL event handlers. See JSDoc comments in `helpers/deckgl/interactions.ts` for implementation details.

Example: `bbox-select.spec.ts`

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

Playwright mouse events don't trigger DeckGL handlers. Use helpers from `helpers/deck-interaction.ts`:

```typescript
import { deckClick, deckHover } from "./helpers/deck-interaction";

await deckClick(page, x, y);  // Calls deck.props.onClick()
await deckHover(page, x, y);  // Calls deck.props.onHover()
```

See `bbox-select.spec.ts` for example usage.

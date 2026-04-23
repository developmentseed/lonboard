# deck.gl 9.3 / deck.gl-raster 0.5 Upgrade

## Goal

Upgrade lonboard's TypeScript dependencies from deck.gl 9.2.11 → 9.3.1 and from the
beta `@developmentseed/deck.gl-raster@0.5.0-beta.1` family to the stable `^0.5.0`
release.

## Current state

`package.json` pins:

- `@deck.gl/*` deps and overrides: `^9.2.11`
- `@luma.gl/*` overrides: `^9.2.6`
- `@developmentseed/deck.gl-raster`, `@developmentseed/affine`,
  `@developmentseed/morecantile`, `@developmentseed/raster-reproject`:
  `^0.5.0-beta.1`

The only source file that imports `@developmentseed/deck.gl-raster` is
[src/model/layer/raster.ts](../../../src/model/layer/raster.ts). deck.gl itself
is used throughout `src/`.

`pnpm-workspace.yaml` and `pnpm-lock.yaml` are untracked local dev artifacts
that `link:` sibling checkouts of the deck.gl-raster monorepo; they are out of
scope.

## Target state

`package.json` pins:

- `@deck.gl/*` deps and overrides: `^9.3.1`
- `@luma.gl/*` overrides: `^9.3.2` (required by deck.gl-raster 0.5 peer deps)
- `@developmentseed/*` 0.5-beta packages: `^0.5.0`

## Approach

1. Edit `package.json` to bump the versions listed above.
2. Run `pnpm install` to refresh `pnpm-lock.yaml` (local dev lockfile).
3. Run `npm run build` and `npm run check`; investigate and fix any TypeScript /
   runtime breakages from the deck.gl 9.3 or deck.gl-raster 0.5 stable APIs. No
   specific migration issues are known upfront — they will be discovered via the
   build.
4. Sanity-check with a relevant Python test (e.g. the raster layer tests under
   `tests/`) to confirm the JS bundle still works end-to-end.

## Out of scope

- Touching `pnpm-workspace.yaml` (local linkage to sibling repos).
- Regenerating `package-lock.json` via `npm install`.
- Broader refactoring of layer code.

## Risks

- deck.gl 9.3 may have type-level breaking changes in widely-used interfaces
  (`TextureSource`, `TileLayerProps`, `_Tileset2DProps`), which could cascade
  through multiple `src/model/layer/*.ts` files.
- deck.gl-raster 0.5 stable may differ from 0.5.0-beta.1 in API shape for
  `RasterLayer` or `TileMatrixSetTileset`, both used in
  `src/model/layer/raster.ts`.

Both risks are addressed by letting `tsc` / biome surface the breakages during
step 3 and fixing them in place.

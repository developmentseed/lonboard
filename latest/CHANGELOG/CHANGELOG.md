# Changelog

## [0.2.0] - 2023-11-01

### Breaking Changes

- Layers no longer render a map object. Instead, pass one or more layer instances into a `lonboard.Map` and display that.

### New Features

- Support multiple layers on a single map.
- Tooltip with data information on hover.
- Allow hex string color input to ColorAccessor.
- Versioned documentation website
- New examples
- Experimental API to change map height

### Fixed

- Fix handling of 3d coordinates by @kylebarron in https://github.com/developmentseed/lonboard/pull/160
- Improved validation error messages by @kylebarron in https://github.com/developmentseed/lonboard/pull/161

### New Contributors

- @chrisgervang made their first contribution in https://github.com/developmentseed/lonboard/pull/150

**Full Changelog**: https://github.com/developmentseed/lonboard/compare/v0.1.2...v0.2.0

## [0.1.2] - 2023-10-24

- _Actually_ update `@geoarrow/deck.gl-layers` to version 0.2.0, whoops 😅

## [0.1.1] - 2023-10-23

- Updates to `@geoarrow/deck.gl-layers` version 0.2.0:
  - Fixed MultiPolygon rendering
  - Fixed rendering of polygons with holes.
  - Polygon rendering is roughly 35% faster.

## [0.1.0] - 2023-10-17

- Initial public release.
- Initial support for `ScatterplotLayer`, `PathLayer`, and `SolidPolygonLayer`.

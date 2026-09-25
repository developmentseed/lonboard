# DuckDB CRS support

**Date:** 2026-06-12
**Branch:** `duckdb-crs`
**Status:** Approved

## Problem

Lonboard has always assumed DuckDB geometry data is in EPSG:4326. DuckDB 1.5's
spatial extension parameterizes the `GEOMETRY` type with a CRS (e.g.
`GEOMETRY('EPSG:3857')`) and its native Arrow export now attaches spec-compliant
GeoArrow metadata: `ARROW:extension:name = geoarrow.wkb` plus
`ARROW:extension:metadata` containing the full PROJJSON CRS. Lonboard should use
that CRS instead of assuming EPSG:4326.

Verified facts (duckdb 1.5.3):

- Only `GEOMETRY` takes a CRS parameter; `WKB_BLOB`, `POINT_2D`,
  `LINESTRING_2D`, `POLYGON_2D`, and `BOX_2D` reject type parameters.
- `rel.arrow()` on a `GEOMETRY` column yields `binary` + `geoarrow.wkb`
  extension name. With a CRS it includes `{"crs_type", "crs"}` (PROJJSON) in the
  extension metadata; without a CRS the extension metadata is empty.
- DuckDB validates the CRS parameter at bind time, so any CRS lonboard receives
  is recognized.
- The current `_from_geometry` path (`ST_AsWKB` + `.arrow()`) returns plain
  binary with no metadata on both 1.4 and 1.5, which is why CRS info is lost
  today.
- Under duckdb 1.4 there is no CRS information anywhere.

## Design

### Conversion path (`lonboard/_geoarrow/_duckdb.py`)

For `GEOMETRY` columns, `_from_geometry` exports via `rel.arrow()` directly and
inspects the geometry field:

- If the field carries `ARROW:extension:name = geoarrow.wkb` (duckdb >= 1.5),
  the table is already spec-compliant GeoArrow (WKB binary + PROJJSON CRS).
  Lonboard's existing downstream machinery — including auto-reprojection to
  EPSG:4326 during layer init — consumes it directly. No type-string parsing,
  no `ST_AsWKB` round-trip, no two-pass select/append.
- If the extension name is absent (duckdb 1.4), fall back to the current
  `ST_AsWKB` path unchanged. Runtime feature detection only; no duckdb version
  checks.

The `WKB_BLOB`, `POINT_2D`, `LINESTRING_2D`, `POLYGON_2D`, and `BOX_2D` paths
are untouched: those types cannot carry a CRS, so the `crs` parameter remains
their only CRS source.

### `crs` parameter semantics (`BaseArrowLayer.from_duckdb`)

| Column CRS | `crs=` passed | Behavior |
| --- | --- | --- |
| present | matches (pyproj equality) | `UserWarning`: passing `crs` is no longer needed with duckdb >= 1.5 when using a `GEOMETRY` type with CRS encoded |
| present | mismatches | raise `ValueError` naming both CRS |
| present | not passed | column CRS used automatically |
| absent | passed | exactly today's behavior, no warning |
| absent | not passed | today's behavior (downstream "No CRS exists on data" warning, 4326 assumed) |

Soft deprecation only: the docstring is rewritten to say the CRS is read
automatically from `GEOMETRY` columns on duckdb >= 1.5 and that `crs=` remains
for `WKB_BLOB`/2D types, older duckdb, and data without an encoded CRS. No
blanket `DeprecationWarning`, since those gaps are real and indefinite.

`viz()` gains no `crs` parameter; it picks up the column CRS automatically via
the same path.

### Error handling

- CRS comparison uses `pyproj.CRS` equality (`CRS.from_user_input(param)` vs
  `CRS.from_json_dict(column_crs)`).
- Mismatch error is a `ValueError` whose message includes both CRS identifiers.

### Testing

All tests must pass under duckdb 1.4.4 (lockfile) and the duckdb tests also
under 1.5.3 (`uv run --with duckdb==1.5.3 pytest tests/test_duckdb.py`). New
tests, skipped on duckdb < 1.5 where they exercise 1.5-only behavior:

1. CRS picked up from `GEOMETRY('EPSG:3857')` and auto-reprojected to 4326.
2. Redundant matching `crs=` emits the `UserWarning`.
3. Mismatching `crs=` raises `ValueError`.
4. No-CRS column + `crs=` works as before, without a warning.

### Out of scope

- Lockfile upgrade (separate PR once this merges).
- CRS support for `WKB_BLOB`/2D types (impossible upstream today).
- Removing the `crs` parameter.

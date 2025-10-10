import { expect } from "@playwright/test";

/**
 * Validates that bounds text contains valid geographic coordinates.
 * Expects format: "Selected bounds: (minLon, minLat, maxLon, maxLat)"
 *
 * @param boundsText - Text output containing bounds coordinates
 * @throws AssertionError if bounds are invalid
 */
export function validateBounds(boundsText: string | null) {
  expect(boundsText, "Expected output to contain coordinates").not.toContain(
    "None",
  );
  expect(boundsText, "Expected output to not be zeros").not.toContain(
    "(0, 0, 0, 0)",
  );

  // Extract and validate the actual bounds values (handles scientific notation and decimals)
  const boundsMatch = boundsText?.match(
    /Selected bounds: \(([-\deE.]+), ([-\deE.]+), ([-\deE.]+), ([-\deE.]+)\)/,
  );
  expect(
    boundsMatch,
    `Expected to find bounds pattern in: ${boundsText}`,
  ).toBeTruthy();
  if (boundsMatch) {
    const [, minLon, minLat, maxLon, maxLat] = boundsMatch.map(Number);

    // Verify we have valid coordinate ranges
    expect(minLon, "minLon should not be zero").not.toBe(0);
    expect(minLat, "minLat should not be zero").not.toBe(0);
    expect(maxLon, "maxLon should not be zero").not.toBe(0);
    expect(maxLat, "maxLat should not be zero").not.toBe(0);

    // Verify min < max for both dimensions
    expect(minLon, "minLon should be less than maxLon").toBeLessThan(maxLon);
    expect(minLat, "minLat should be less than maxLat").toBeLessThan(maxLat);

    // Verify coordinates are within valid lat/lon ranges
    expect(minLon, "minLon should be >= -180").toBeGreaterThanOrEqual(-180);
    expect(maxLon, "maxLon should be <= 180").toBeLessThanOrEqual(180);
    expect(minLat, "minLat should be >= -90").toBeGreaterThanOrEqual(-90);
    expect(maxLat, "maxLat should be <= 90").toBeLessThanOrEqual(90);
  }
}

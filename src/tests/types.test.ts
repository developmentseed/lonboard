import { describe, expect, it } from "vitest";

import { accessColorData, accessFloatData } from "../model/types.js";

describe("accessColorData", () => {
  it("returns undefined for an unset accessor", () => {
    expect(accessColorData(null, 0)).toBeUndefined();
    expect(accessColorData(undefined, 0)).toBeUndefined();
  });

  it("returns a constant color as-is", () => {
    expect(accessColorData([255, 0, 0], 0)).toEqual([255, 0, 0]);
  });
});

describe("accessFloatData", () => {
  it("returns undefined for an unset accessor", () => {
    expect(accessFloatData(null, 0)).toBeUndefined();
    expect(accessFloatData(undefined, 0)).toBeUndefined();
  });

  it("returns a constant of 0 as-is", () => {
    expect(accessFloatData(0, 0)).toBe(0);
  });
});

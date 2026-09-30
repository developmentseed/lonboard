import { describe, expect, it } from "vitest";

import { omitUndefined } from "../util.js";

describe("omitUndefined", () => {
  it("drops keys whose value is undefined or null", () => {
    expect(omitUndefined({ a: 1, b: undefined, c: null })).toEqual({ a: 1 });
  });

  it("keeps falsy values that are not null or undefined", () => {
    const props = { a: 0, b: false, c: "" };
    expect(omitUndefined(props)).toEqual(props);
  });
});

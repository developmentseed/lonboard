import { describe, expect, it } from "vitest";

import { moveViewState, omitUndefined } from "../util.js";

describe("omitUndefined", () => {
  it("drops keys whose value is undefined or null", () => {
    expect(omitUndefined({ a: 1, b: undefined, c: null })).toEqual({ a: 1 });
  });

  it("keeps falsy values that are not null or undefined", () => {
    const props = { a: 0, b: false, c: "" };
    expect(omitUndefined(props)).toEqual(props);
  });
});

describe("moveViewState", () => {
  const camera = {
    longitude: 10,
    latitude: 20,
    zoom: 5,
    pitch: 30,
    bearing: 45,
  };

  it("moves the camera and keeps the other keys", () => {
    const current = {
      longitude: 0,
      latitude: 0,
      zoom: 3,
      pitch: 0,
      bearing: 0,
      maxZoom: 12,
      minZoom: 2,
      maxPitch: 60,
      minPitch: 0,
    };
    expect(moveViewState(current, camera)).toEqual({
      ...camera,
      maxZoom: 12,
      minZoom: 2,
      maxPitch: 60,
      minPitch: 0,
    });
  });

  it("doesn't add keys that the view state doesn't have", () => {
    // A globe view state has no pitch or bearing
    const current = { longitude: 0, latitude: 0, zoom: 3, maxZoom: 20 };
    expect(moveViewState(current, camera)).toEqual({
      longitude: 10,
      latitude: 20,
      zoom: 5,
      maxZoom: 20,
    });
  });

  it("drops transition keys, which Python doesn't keep", () => {
    const current = {
      longitude: 0,
      latitude: 0,
      zoom: 3,
      transitionDuration: 4000,
      transitionInterpolator: {},
    };
    expect(moveViewState(current, camera)).toEqual({
      longitude: 10,
      latitude: 20,
      zoom: 5,
    });
  });

  it("returns the camera when there is no view state", () => {
    expect(moveViewState(null, camera)).toEqual(camera);
  });
});

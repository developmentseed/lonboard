import type { AffineTilesetLevelOptions } from "@developmentseed/deck.gl-raster";
import { AffineTileset } from "@developmentseed/deck.gl-raster";
import { describe, expect, it, vi } from "vitest";

import { RasterModel } from "../model/layer/raster.js";
import { FakeWidgetModel } from "./fake-widget-model.js";

const LEVEL: AffineTilesetLevelOptions = {
  affine: [1, 0, -180, 0, -1, 90],
  arrayWidth: 360,
  arrayHeight: 180,
  tileWidth: 512,
  tileHeight: 512,
  mpu: 111319.4907932736,
};

describe("RasterModel affine levels", () => {
  it("builds an AffineTileset from _affine_levels", () => {
    const model = new FakeWidgetModel({
      _crs: "EPSG:4326",
      _affine_levels: [LEVEL],
    });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    const tileset = raster.affineTileset();

    expect(tileset).toBeInstanceOf(AffineTileset);
    expect(tileset!.levels).toHaveLength(1);
    expect(tileset!.levels[0].matrixWidth).toBe(1);
    expect(tileset!.projectedBounds).toEqual([-180, -90, 180, 90]);
  });

  it("orders levels coarsest first and maps tile z back to the Python index", () => {
    const fine: AffineTilesetLevelOptions = {
      ...LEVEL,
      affine: [0.5, 0, -180, 0, -0.5, 90],
      arrayWidth: 720,
      arrayHeight: 360,
    };
    const model = new FakeWidgetModel({
      _crs: "EPSG:4326",
      // Finest first, the opposite of what deck.gl-raster expects
      _affine_levels: [fine, LEVEL],
    });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    const tileset = raster.affineTileset();

    expect(tileset!.levels.map((l) => l.matrixWidth)).toEqual([1, 2]);
    expect(raster.pythonLevelIndex(0)).toBe(1);
    expect(raster.pythonLevelIndex(1)).toBe(0);
  });

  it("returns null without levels", () => {
    const model = new FakeWidgetModel({
      _crs: "EPSG:4326",
      _affine_levels: null,
    });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    expect(raster.affineTileset()).toBeNull();
  });

  it("keeps the same tileset across calls and rebuilds when the levels change", () => {
    const model = new FakeWidgetModel({
      _crs: "EPSG:4326",
      _affine_levels: [LEVEL],
    });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    const first = raster.affineTileset();
    expect(raster.affineTileset()).toBe(first);

    model.set("_affine_levels", [{ ...LEVEL, tileWidth: 256 }]);
    const second = raster.affineTileset();
    expect(second).not.toBe(first);
    expect(second!.levels[0].matrixWidth).toBe(2);
  });
});

import type { WidgetModel } from "@jupyter-widgets/base";
import { describe, expect, it, vi } from "vitest";

import { BaseModel } from "../model/base.js";
import { BaseLayerModel } from "../model/layer/base.js";
import { RasterModel } from "../model/layer/raster.js";
import { FakeWidgetModel } from "./fake-widget-model.js";

class OpacityModel extends BaseModel {
  opacity: number | undefined;

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

    this.initRegularAttribute("opacity", "opacity");
  }
}

class TestLayerModel extends BaseLayerModel {
  layerProps() {
    return { id: "test" };
  }

  render() {
    return [];
  }
}

describe("BaseModel", () => {
  it("follows changes on the Jupyter model", () => {
    const model = new FakeWidgetModel({ opacity: 1 });
    const updateState = vi.fn();
    const wrapper = new OpacityModel(model.asWidgetModel(), updateState);

    model.set("opacity", 0.5);

    expect(wrapper.opacity).toBe(0.5);
    expect(updateState).toHaveBeenCalledTimes(1);
  });

  it("stops following changes after finalize", () => {
    const model = new FakeWidgetModel({ opacity: 1 });
    const updateState = vi.fn();
    const wrapper = new OpacityModel(model.asWidgetModel(), updateState);

    wrapper.finalize();
    model.set("opacity", 0.5);

    expect(wrapper.opacity).toBe(1);
    expect(updateState).not.toHaveBeenCalled();
  });

  it("leaves other listeners on the Jupyter model in place on finalize", () => {
    const model = new FakeWidgetModel({ opacity: 1 });
    const wrapper = new OpacityModel(model.asWidgetModel(), vi.fn());
    const otherListener = vi.fn();
    model.on("change", otherListener);

    wrapper.finalize();
    model.set("opacity", 0.5);

    expect(otherListener).toHaveBeenCalledTimes(1);
  });
});

describe("BaseLayerModel", () => {
  it("stops following its extensions after finalize", async () => {
    const extensionModel = new FakeWidgetModel({ _extension_type: "brushing" });
    const layerModel = new FakeWidgetModel(
      { extensions: ["IPY_MODEL_extension-id"] },
      { "extension-id": extensionModel },
    );
    const updateState = vi.fn();
    const layer = new TestLayerModel(layerModel.asWidgetModel(), updateState);
    await layer.loadSubModels();

    // Before finalize, a change on the extension updates the map
    extensionModel.set("some_attribute", 1);
    expect(updateState).toHaveBeenCalledTimes(1);

    updateState.mockClear();
    layer.finalize();
    extensionModel.set("some_attribute", 2);

    expect(updateState).not.toHaveBeenCalled();
  });
});

describe("RasterModel", () => {
  it("updates its CRS converters when the CRS changes", () => {
    const model = new FakeWidgetModel({ _crs: "EPSG:3857" });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    model.set("_crs", "EPSG:4326");

    expect(raster.accessConverters().forwardTo4326(10, 20)).toEqual([10, 20]);
  });

  it("stops updating its CRS converters after finalize", () => {
    const model = new FakeWidgetModel({ _crs: "EPSG:4326" });
    const raster = new RasterModel(model.asWidgetModel(), vi.fn());

    raster.finalize();
    model.set("_crs", "EPSG:3857");

    expect(raster.accessConverters().forwardTo4326(10, 20)).toEqual([10, 20]);
  });
});

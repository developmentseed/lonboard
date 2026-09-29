import type { Layer } from "@deck.gl/core";
import type { TileLayerProps } from "@deck.gl/geo-layers";
import { describe, expect, it, vi } from "vitest";

import { BitmapTileModel } from "../model/layer/bitmap.js";
import { FakeWidgetModel } from "./fake-widget-model.js";

type SubLayerProps = Parameters<
  NonNullable<TileLayerProps["renderSubLayers"]>
>[0];

/**
 * The props that a `TileLayer` passes to `renderSubLayers` for one tile. It
 * gives each tile's sub-layer an id of its own.
 */
function subLayerProps(id: string): SubLayerProps {
  return {
    id,
    data: null,
    tile: {
      boundingBox: [
        [0, 0],
        [1, 1],
      ],
    },
  } as unknown as SubLayerProps;
}

describe("BitmapTileModel", () => {
  it("keeps the id that the tile layer gives each tile's sub-layer", () => {
    const model = new FakeWidgetModel({
      data: "https://example.com/{z}/{x}/{y}.png",
    });
    const tileLayer = new BitmapTileModel(
      model.asWidgetModel(),
      vi.fn(),
    ).render();
    const renderSubLayers = tileLayer.props.renderSubLayers;

    const subLayers = ["tiles-0-0-1", "tiles-1-0-1"].map(
      (id) => renderSubLayers(subLayerProps(id)) as Layer,
    );

    expect(subLayers.map((layer) => layer.id)).toEqual([
      "tiles-0-0-1",
      "tiles-1-0-1",
    ]);
  });
});

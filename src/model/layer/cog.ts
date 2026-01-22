import type { WidgetModel } from "@jupyter-widgets/base";
import {TileLayer, TileLayerProps} from "@deck.gl/geo-layers"

import {  BaseLayerModel } from "./base.js";
import { invoke } from "../invoke.js";

export class COGModel extends BaseLayerModel {
  static layerType = "cog";

  constructor(model: WidgetModel, updateStateCallback: () => void) {
    super(model, updateStateCallback);

  }

  getTileData: TileLayerProps["getTileData"] = async (tile) => {
    const {index, id, bbox} = tile;
    const { signal } = tile;
    console.log("in getTileData");

    console.log("calling invoke");
    console.log(tile);
    const [message, buffer] = await invoke(
      this.model,
      {
        tile_id: tile.id,
      },
      "cog-get-tile-data",
      { signal, timeout: 10000 },
    );

    console.log("returned from invoke, message and buffer received", message, buffer);

    if (signal?.aborted) {
      return null;
    }


    console.log("returned from invoke");
    console.log(message);

    return null;
  };

  layerProps(): TileLayerProps {
    return {
      id: `${this.model.model_id}`,
      data: null,
    };
  }

  render(): TileLayer  {
    return new TileLayer({
      ...this.baseLayerProps(),
      ...this.layerProps(),
      getTileData: this.getTileData?.bind(this),
      renderSubLayers: (props) => {
        return null;
      }
    })
  }
}

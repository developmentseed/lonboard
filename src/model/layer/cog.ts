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
    const { signal } = tile;
    const signals: AbortSignal[] = [AbortSignal.timeout(10_000)];
    if (signal !== undefined) {
      signals.push(signal);
    }

    const compositeSignal = AbortSignal.any(signals);
    console.log("in getTileData");

    console.log("calling invoke");
    console.log(tile);
    const [message, buffer] = await invoke(
      this.model,
      {
        tile_id: tile.id,
      },
      { signal: compositeSignal },
    );

    if (compositeSignal.aborted) {
      return null;
    }

    if (buffer.length === 0) {
      return null;
    }

    console.log("returned from invoke");
    console.log(message);
    console.log(buffer.length);
    console.log(buffer[0]);
    console.log(buffer[0].byteLength);
    console.log(tile);

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
        console.log("in renderSubLayers");
        console.log(props);
        return null;
      }
    })
  }
}

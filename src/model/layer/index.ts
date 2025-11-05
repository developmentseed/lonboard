import { WidgetModel } from "@jupyter-widgets/base";

import { ArcModel } from "./arc.js";
import { BaseLayerModel } from "./base.js";
import { BitmapModel, BitmapTileModel } from "./bitmap.js";
import { ColumnModel } from "./column.js";
import { HeatmapModel } from "./heatmap.js";
import { PathModel } from "./path.js";
import { PointCloudModel } from "./point-cloud.js";
import {
  A5Model,
  GeohashModel,
  H3HexagonModel,
  PolygonModel,
  S2Model,
  SolidPolygonModel,
} from "./polygon.js";
import { ScatterplotModel } from "./scatterplot.js";
import { SurfaceModel } from "./surface.js";
import { TextModel } from "./text.js";
import { TripsModel } from "./trips.js";

export { ArcModel } from "./arc.js";
export { BitmapModel, BitmapTileModel } from "./bitmap.js";
export { ColumnModel } from "./column.js";
export { HeatmapModel } from "./heatmap.js";
export { PathModel } from "./path.js";
export { PointCloudModel } from "./point-cloud.js";
export {
  A5Model,
  H3HexagonModel,
  PolygonModel,
  SolidPolygonModel,
} from "./polygon.js";
export { ScatterplotModel } from "./scatterplot.js";
export { SurfaceModel } from "./surface.js";
export { TextModel } from "./text.js";
export { TripsModel } from "./trips.js";

export async function initializeLayer(
  model: WidgetModel,
  updateStateCallback: () => void,
): Promise<BaseLayerModel> {
  const layerType = model.get("_layer_type");
  let layerModel: BaseLayerModel;
  switch (layerType) {
    case A5Model.layerType:
      layerModel = new A5Model(model, updateStateCallback);
      break;

    case ArcModel.layerType:
      layerModel = new ArcModel(model, updateStateCallback);
      break;

    case BitmapModel.layerType:
      layerModel = new BitmapModel(model, updateStateCallback);
      break;

    case BitmapTileModel.layerType:
      layerModel = new BitmapTileModel(model, updateStateCallback);
      break;

    case ColumnModel.layerType:
      layerModel = new ColumnModel(model, updateStateCallback);
      break;

    case GeohashModel.layerType:
      layerModel = new GeohashModel(model, updateStateCallback);
      break;

    case H3HexagonModel.layerType:
      layerModel = new H3HexagonModel(model, updateStateCallback);
      break;

    case HeatmapModel.layerType:
      layerModel = new HeatmapModel(model, updateStateCallback);
      break;

    case PathModel.layerType:
      layerModel = new PathModel(model, updateStateCallback);
      break;

    case PointCloudModel.layerType:
      layerModel = new PointCloudModel(model, updateStateCallback);
      break;

    case PolygonModel.layerType:
      layerModel = new PolygonModel(model, updateStateCallback);
      break;

    case S2Model.layerType:
      layerModel = new S2Model(model, updateStateCallback);
      break;

    case ScatterplotModel.layerType:
      layerModel = new ScatterplotModel(model, updateStateCallback);
      break;

    case SolidPolygonModel.layerType:
      layerModel = new SolidPolygonModel(model, updateStateCallback);
      break;

    case SurfaceModel.layerType:
      layerModel = new SurfaceModel(model, updateStateCallback);
      break;

    case TextModel.layerType:
      layerModel = new TextModel(model, updateStateCallback);
      break;

    case TripsModel.layerType:
      layerModel = new TripsModel(model, updateStateCallback);
      break;

    default:
      throw new Error(`no layer supported for ${layerType}`);
  }

  await layerModel.loadSubModels();
  return layerModel;
}

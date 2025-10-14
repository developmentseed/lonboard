import type { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import type { BaseModel } from "./base";

// childModelId is of the form "IPY_MODEL_<identifier>"
// https://github.com/jupyter-widgets/ipywidgets/blob/8.1.7/packages/schema/jupyterwidgetmodels.v8.md
const IPY_MODEL_ = "IPY_MODEL_";

// We need to slice off the "IPY_MODEL_" prefix to get the actual model ID
const IPY_MODEL_LENGTH = IPY_MODEL_.length;

/**
 * Load and initialize the child models of this model.
 *
 * @param widget_manager The widget manager used to load the models.
 * @param childModelIds The model IDs of the child models to load.
 * @param previousSubModelState Any previously loaded child models. Models that are still present will be reused. Any reactivity on _those models_ will be handled separately.
 * @param initializer A function that takes a WidgetModel and returns an initialized model of type T.
 *
 * @return A promise that resolves to a mapping from model ID to initialized model.
 */
export async function initializeChildModels<T extends BaseModel>(
  widget_manager: IWidgetManager,
  childModelIds: string[],
  previousSubModelState: Record<string, T>,
  initializer: (model: WidgetModel) => Promise<T>,
): Promise<Record<string, T>> {
  const childModels = await loadModels(widget_manager, childModelIds);

  const newSubModelState: Record<string, T> = {};

  for (const [childModelId, childModel] of Object.entries(childModels)) {
    // If the layer existed previously, copy its model without constructing
    // a new one
    if (childModelId in previousSubModelState) {
      // pop from old state
      newSubModelState[childModelId] = previousSubModelState[childModelId];
      delete previousSubModelState[childModelId];
    }

    // TODO: should we be using Promise.all here?
    newSubModelState[childModelId] = await initializer(childModel);
  }

  // finalize models that were deleted
  for (const previousChildModel of Object.values(previousSubModelState)) {
    previousChildModel.finalize();
  }

  return newSubModelState;
}

/**
 * Load and resolve other widget models.
 *
 * Loading of models is asynchronous; we load all models in parallel.
 */
async function loadModels(
  widget_manager: IWidgetManager,
  childModelIds: string[],
): Promise<Record<string, WidgetModel>> {
  const promises = childModelIds.map((childModelId) => {
    // We need to slice off the "IPY_MODEL_" prefix to get the actual model ID
    const modelId = childModelId.slice(IPY_MODEL_LENGTH);
    return widget_manager.get_model(modelId);
  });

  const models = await Promise.all(promises);

  const returnedModels: Record<string, WidgetModel> = {};
  for (let i = 0; i < childModelIds.length; i++) {
    returnedModels[childModelIds[i]] = models[i];
  }
  return returnedModels;
}

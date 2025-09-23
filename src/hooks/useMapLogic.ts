import { useCallback, useEffect, useState } from "react";
import { MapViewState, PickingInfo, type Layer } from "@deck.gl/core";
import { BaseLayerModel, initializeLayer } from "../model/index.js";
import type { WidgetModel } from "@jupyter-widgets/base";
import { useModelState, useModel } from "@anywidget/react";
import { loadChildModels } from "../util.js";
import { Message } from "../types.js";
import { flyTo } from "../actions/fly-to.js";
import { useViewStateDebounced } from "../state";
import throttle from "lodash.throttle";
import { MachineContext } from "../xstate";
import * as selectors from "../xstate/selectors";

async function getChildModelState(
  childModels: WidgetModel[],
  childLayerIds: string[],
  previousSubModelState: Record<string, BaseLayerModel>,
  setStateCounter: React.Dispatch<React.SetStateAction<Date>>,
): Promise<Record<string, BaseLayerModel>> {
  const newSubModelState: Record<string, BaseLayerModel> = {};
  const updateStateCallback = () => setStateCounter(new Date());

  for (let i = 0; i < childLayerIds.length; i++) {
    const childLayerId = childLayerIds[i];
    const childModel = childModels[i];

    if (childLayerId in previousSubModelState) {
      newSubModelState[childLayerId] = previousSubModelState[childLayerId];
      delete previousSubModelState[childLayerId];
      continue;
    }

    const childLayer = await initializeLayer(childModel, updateStateCallback);
    newSubModelState[childLayerId] = childLayer;
  }

  for (const previousChildModel of Object.values(previousSubModelState)) {
    previousChildModel.finalize();
  }

  return newSubModelState;
}

export function useMapLogic() {
  const actorRef = MachineContext.useActorRef();
  const isDrawingBBoxSelection = MachineContext.useSelector(
    selectors.isDrawingBBoxSelection,
  );
  const isOnMapHoverEventEnabled = MachineContext.useSelector(
    selectors.isOnMapHoverEventEnabled,
  );
  const bboxSelectBounds = MachineContext.useSelector(
    selectors.getBboxSelectBounds,
  );

  const [justClicked, setJustClicked] = useState<boolean>(false);
  const model = useModel();

  const [initialViewState, setViewState] =
    useViewStateDebounced<MapViewState>("view_state");

  const [subModelState, setSubModelState] = useState<
    Record<string, BaseLayerModel>
  >({});
  const [childLayerIds] = useModelState<string[]>("layers");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [stateCounter, setStateCounter] = useState<Date>(new Date());

  // Handle custom messages
  model.on("msg:custom", (msg: Message) => {
    switch (msg.type) {
      case "fly-to":
        flyTo(msg, setViewState);
        break;
      default:
        break;
    }
  });

  useEffect(() => {
    const loadAndUpdateLayers = async () => {
      try {
        const childModels = await loadChildModels(
          model.widget_manager,
          childLayerIds,
        );

        const newSubModelState = await getChildModelState(
          childModels,
          childLayerIds,
          subModelState,
          setStateCounter,
        );
        setSubModelState(newSubModelState);

        if (!isDrawingBBoxSelection) {
          model.set("selected_bounds", bboxSelectBounds);
          model.save_changes();
        }
      } catch (error) {
        console.error("Error loading child models or setting bounds:", error);
      }
    };

    loadAndUpdateLayers();
  }, [childLayerIds, bboxSelectBounds, isDrawingBBoxSelection]);

  const layers: Layer[] = [];
  for (const subModel of Object.values(subModelState)) {
    layers.push(subModel.render());
  }

  const onMapClickHandler = useCallback((info: PickingInfo) => {
    if (typeof info.coordinate !== "undefined") {
      if (model.get("_has_click_handlers")) {
        model.send({ kind: "on-click", coordinate: info.coordinate });
      }
    }
    setJustClicked(true);
    actorRef.send({
      type: "Map click event",
      data: info,
    });
    setTimeout(() => {
      setJustClicked(false);
    }, 100);
  }, []);

  const onMapHoverHandler = useCallback(
    throttle(
      (info: PickingInfo) =>
        isOnMapHoverEventEnabled &&
        !justClicked &&
        actorRef.send({
          type: "Map hover event",
          data: info,
        }),
      100,
    ),
    [isOnMapHoverEventEnabled, justClicked],
  );

  const onViewStateChange = useCallback((event: { viewState: any }) => {
    const { viewState } = event;
    if ("latitude" in viewState) {
      const { longitude, latitude, zoom, pitch, bearing } = viewState;
      setViewState({
        longitude,
        latitude,
        zoom,
        pitch,
        bearing,
      });
    }
  }, [setViewState]);

  return {
    layers,
    initialViewState,
    onMapClickHandler,
    onMapHoverHandler,
    onViewStateChange,
    isDrawingBBoxSelection,
  };
}
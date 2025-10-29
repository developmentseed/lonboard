import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import React from "react";

import { SquareIcon, XMarkIcon } from "./icons";
import { MachineContext } from "./xstate";
import * as selectors from "./xstate/selectors";

const Toolbar: React.FC = () => {
  const actorRef = MachineContext.useActorRef();
  const isDrawingBBoxSelection = MachineContext.useSelector(
    selectors.isDrawingBBoxSelection,
  );
  const isBboxDefined = MachineContext.useSelector(
    (state) => state.context.bboxSelectStart && state.context.bboxSelectEnd,
  );

  const handleButtonClick = () => {
    if (isDrawingBBoxSelection) {
      actorRef.send({ type: "Cancel BBox draw" });
    } else if (isBboxDefined) {
      actorRef.send({ type: "Clear BBox" });
    } else {
      actorRef.send({ type: "BBox select button clicked" });
    }
  };

  return (
    <div
      style={{
        position: "absolute",
        bottom: "20px",
        right: "20px",
        zIndex: 1000,
        backgroundColor: "white",
        borderRadius: "8px",
        boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
        padding: "4px",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: "4px",
      }}
    >
      <ButtonGroup variant="flat">
        <Tooltip
          content={
            isDrawingBBoxSelection
              ? "Cancel drawing"
              : isBboxDefined
                ? "Clear bounding box"
                : "Start bounding box selection"
          }
          placement="bottom"
        >
          <Button
            isIconOnly
            aria-label={
              isDrawingBBoxSelection
                ? "Cancel drawing"
                : isBboxDefined
                  ? "Clear bounding box"
                  : "Select BBox"
            }
            color={
              isDrawingBBoxSelection
                ? "warning"
                : isBboxDefined
                  ? "danger"
                  : "default"
            }
            onClick={handleButtonClick}
          >
            {isDrawingBBoxSelection || isBboxDefined ? (
              <XMarkIcon />
            ) : (
              <SquareIcon />
            )}
          </Button>
        </Tooltip>
      </ButtonGroup>
    </div>
  );
};

export default Toolbar;

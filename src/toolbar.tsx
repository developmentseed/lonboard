import React from "react";
import { MachineContext } from "./state/index.js";
import * as selectors from "./state/selectors.js";
import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import { SquareIcon } from "./icons/square";

const Toolbar: React.FC = () => {
  const actorRef = MachineContext.useActorRef();
  const isDrawingBBoxSelection = MachineContext.useSelector(
    selectors.isDrawingBBoxSelection,
  );
  const isBboxDefined = MachineContext.useSelector(
    (state) => state.context.bboxSelectStart && state.context.bboxSelectEnd,
  );

  const handleBBoxAction = () => {
    if (isBboxDefined) {
      actorRef.send({ type: "Clear BBox" });
    } else {
      actorRef.send({ type: "BBox select button clicked" });
    }
  };

  return (
    <div
      style={{
        position: "absolute",
        top: "20px",
        right: "20px",
        zIndex: 1000,
        backgroundColor: "white",
        borderRadius: "4px",
        boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
        padding: "4px",
      }}
    >
      <ButtonGroup variant="light">
        <Tooltip
          content={
            isBboxDefined
              ? "Clear bounding box"
              : "Start bounding box selection"
          }
          placement="bottom"
        >
          <Button
            isIconOnly
            aria-label={isBboxDefined ? "Clear BBox" : "Select BBox"}
            variant={isDrawingBBoxSelection || isBboxDefined ? "flat" : "light"}
            onClick={handleBBoxAction}
          >
            <SquareIcon />
          </Button>
        </Tooltip>
      </ButtonGroup>
    </div>
  );
};

export default Toolbar;

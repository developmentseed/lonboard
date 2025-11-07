import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import React from "react";

import { SquareIcon, XMarkIcon } from "./icons";
import { useStore } from "./store";

const Toolbar: React.FC = () => {
  const isDrawingBbox = useStore((state) => state.isDrawingBbox);
  const bboxSelectStart = useStore((state) => state.bboxSelectStart);
  const bboxSelectEnd = useStore((state) => state.bboxSelectEnd);
  const startBboxSelection = useStore((state) => state.startBboxSelection);
  const cancelBboxSelection = useStore((state) => state.cancelBboxSelection);
  const clearBboxSelection = useStore((state) => state.clearBboxSelection);

  const isBboxDefined = bboxSelectStart && bboxSelectEnd;

  const handleButtonClick = () => {
    if (isDrawingBbox) {
      cancelBboxSelection();
    } else if (isBboxDefined) {
      clearBboxSelection();
    } else {
      startBboxSelection();
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
            isDrawingBbox
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
              isDrawingBbox
                ? "Cancel drawing"
                : isBboxDefined
                  ? "Clear bounding box"
                  : "Select BBox"
            }
            color={
              isDrawingBbox
                ? "warning"
                : isBboxDefined
                  ? "danger"
                  : "default"
            }
            onClick={handleButtonClick}
          >
            {isDrawingBbox || isBboxDefined ? (
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

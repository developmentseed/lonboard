import React from "react";
import type { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import "./index.css";

const rowIndexSymbol = Symbol.for("rowIndex");

interface TooltipProps {
  info: GeoArrowPickingInfo;
}

const Tooltip: React.FC<TooltipProps> = ({ info }) => {
  const { object, x, y } = info;

  if (
    !object ||
    object[rowIndexSymbol] === null ||
    object[rowIndexSymbol] === undefined ||
    (object[rowIndexSymbol] && object[rowIndexSymbol] < 0)
  ) {
    return null;
  }

  const jsonObj = object.toJSON?.() || object;
  if (!jsonObj || typeof jsonObj !== "object") {
    return null;
  }

  const { ...featureProperties } = jsonObj;

  if (Object.keys(featureProperties).length === 0) {
    return null;
  }

  // Prevent scroll events on the tooltip from propagating to the map
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.stopPropagation();
    e.preventDefault();
  };

  // Prevent pointer events from propagating to the map
  const handlePointerEvent = (e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
  };

  return (
    <div
      className="lonboard-tooltip"
      style={{
        position: "absolute",
        backgroundColor: "#fff",
        boxShadow: "0 0 15px rgba(0, 0, 0, 0.1)",
        color: "#000",
        padding: "6px",
        left: `${x}px`,
        top: `${y}px`,
        pointerEvents: "auto",
        zIndex: 1000,
      }}
      // Prevent mouse events from propagating to the map
      onClick={handlePointerEvent}
      onPointerDown={handlePointerEvent}
      onPointerUp={handlePointerEvent}
      onPointerMove={handlePointerEvent}
    >
      <table
        onWheel={handleWheel} // Handle scroll without propagating to the map
      >
        <tbody>
          {Object.entries(featureProperties)
            .filter(([key]) => key !== "geometry") // Don't show geometry in the tooltip
            .map(([key, value]) => (
              <tr key={key}>
                <td>{key}</td>
                <td>{String(value)}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
};

export default Tooltip;

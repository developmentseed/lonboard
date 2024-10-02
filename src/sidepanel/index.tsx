import React from "react";
import type { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import { XMarkIcon } from "../icons";
import { Button } from "@nextui-org/react";

const rowIndexSymbol = Symbol.for("rowIndex");

interface SidePanelProps {
  info: GeoArrowPickingInfo;
  onClose: () => void;
}

const Header = ({ onClose }: { onClose: () => void }) => (
  <div className="pl-4 py-3 flex justify-between items-center border-b border-default-300 bg-default-100">
    <div className="font-bold text-lg">Feature properties</div>
    <Button
      onClick={onClose}
      variant="flat"
      isIconOnly
      className="bg-default-100"
    >
      <XMarkIcon />
    </Button>
  </div>
);

const SidePanel: React.FC<SidePanelProps> = ({ info, onClose }) => {
  const { object } = info;

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

  return (
    <div className="bg-white shadow-md text-black h-full max-w-1/2 min-w-fit overflow-y-auto overflow-x-hidden box-border">
      <Header onClose={onClose} />
      <table className="table-auto w-full">
        <tbody>
          {Object.entries(featureProperties)
            .filter(([key]) => key !== "geometry")
            .map(([key, value], index) => (
              <tr
                key={key}
                className={index % 2 === 0 ? "bg-white" : "bg-gray-100"}
              >
                <td className="border border-gray-300 px-4 py-2 font-medium">
                  {key}
                </td>
                <td className="border border-gray-300 px-4 py-2">
                  {String(value)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
};

export default SidePanel;

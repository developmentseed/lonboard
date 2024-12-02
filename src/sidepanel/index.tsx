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
    <div className="bg-white shadow-md text-black h-full w-96 overflow-y-auto overflow-x-hidden box-border mr-1">
      <Header onClose={onClose} />
      <table className="w-full border-collapse [&_td]:block">
        <tbody className="grid grid-cols-[minmax(0,_2fr)_minmax(0,_3fr)]">
          {Object.entries(featureProperties)
            .filter(([key]) => key !== "geometry")
            .map(([key, value], index) => (
              <React.Fragment key={key}>
                <td
                  className={`border border-gray-300 px-4 py-2 font-medium ${index % 2 === 0 ? "bg-white" : "bg-gray-100"}`}
                >
                  <div className="truncate" title={key}>
                    {key}
                  </div>
                </td>
                <td
                  className={`border border-gray-300 px-4 py-2 ${index % 2 === 0 ? "bg-white" : "bg-gray-100"}`}
                >
                  <div className="break-words" title={String(value)}>
                    {String(value)}
                  </div>
                </td>
              </React.Fragment>
            ))}
        </tbody>
      </table>
    </div>
  );
};

export default SidePanel;

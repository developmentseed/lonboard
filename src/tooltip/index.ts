import { TooltipContent } from "@deck.gl/core/src/lib/tooltip.js";
import type { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";

import "./index.css";

const rowIndexSymbol = Symbol.for("rowIndex");

function toHtmlTable(featureProperties: Record<string, any>): string {
  return `<table>
      <tbody>
        ${Object.keys(featureProperties)
          .map((key) => {
            const value = featureProperties[key];
            return `<tr>
              <td>${key}</td>
              <td>${value}</td>
            </tr>`;
          })
          .join("")}
      </tbody>
    </table>`;
}

export function getTooltip({ object }: GeoArrowPickingInfo): TooltipContent {
  if (object) {
    // If the row index is -1 or undefined, return
    //
    // Note that this is a private API, but this appears to be the only way to
    // get this information
    //
    // Without this block, we end up showing a tooltip even when not hovering
    // over a point
    if (
      object[rowIndexSymbol] === null ||
      object[rowIndexSymbol] === undefined ||
      (object[rowIndexSymbol] && object[rowIndexSymbol] < 0)
    ) {
      return null;
    }

    const jsonObj = object.toJSON();

    if (!jsonObj) {
      return null;
    }

    delete jsonObj["geometry"];

    if (Object.keys(jsonObj).length === 0) {
      return null;
    }

    return {
      className: "lonboard-tooltip",
      html: toHtmlTable(jsonObj),
      style: {
        backgroundColor: "#fff",
        boxShadow: "0 0 15px rgba(0, 0, 0, 0.1)",
        color: "#000",
        padding: "6px",
      },
    };
  }

  return null;
}

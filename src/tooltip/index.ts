import { TooltipContent } from "@deck.gl/core/typed/lib/tooltip";
import { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers/dist/types";

import "./index.css";

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

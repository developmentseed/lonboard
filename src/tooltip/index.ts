import { PickingInfo } from "@deck.gl/core/typed";
import { TooltipContent } from "@deck.gl/core/typed/lib/tooltip";

import "./index.css";

export function getTooltip({ object }: PickingInfo): TooltipContent {
  if (object) {
    const sampleFeature = {
      timestamp: new Date().toISOString(),
      url: "https://github.com/developmentseed/lonboard/",
      version: 1.2,
      isPublished: true,
      tags: ["open-source", "lonboard", "repo"],
      geometryType: "Point",
      contributors: null,
      integer: 9007199254740991,
    };

    function toHtmlTable(featureProperties) {
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

    return {
      html: `<div class="lonboard-tooltip">${toHtmlTable(sampleFeature)}</div>`,
    };
  }
}

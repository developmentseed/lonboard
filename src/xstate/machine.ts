import { assign, createMachine } from "xstate";
import { PickingInfo } from "@deck.gl/core";
import { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoAFHdAAgFtUIwBiAIQdQA9zYxkwBjAF3MwBXXrwzluyAJbcA1pADaABgC6iUAAdUsSb0kY1IFogC0AJgAcATkKKAbABZzARnMBWe09e3Lt1wBoQAE9EJwB2UJsAZlDXS1DIxVdQuMVTAF80gLQsXAISMioaegBhLnxyJlYlVSQQTW1dfVqjBHNTQlMwxUdTZMtUtwDghGNbQic4z1CnSO97JMcMrIxsfCIAZU4eXXQoAWw2WF58fnqdPXQ6AFkcdXEpWXIwADcwdF5qgzPG9AMWsyShGmwKcFkUkX6-iCiAhkUI5kU4NMsUsnks5gcSxA2VWeU2XD4kl2+1Y7GOeFOWnOGDoxTI3E4FWYbAgeBwAHdPrVvhc-iZHPZCJFIp07PZIk5bPFzENEKZeoRXK5OuZ7BZbKZ0eKsTjchstoTiZgDk90BByDyaTc7gALVCvPBPV7vLkaKk-PkIMJAywQxShZxORL2RSg2UIDyuRWI+JOOPi2x2HUrPWEfHbIl7Y2kt7my2Xa33aQyJ1vD4qL7u3nNEKhMbRGJWHzRNy2cOmByEez2dEi2KKKzmZM5NZpg07LMm3MWqs0unoBnIJmk1kc111We-GsjVzmOE+OuhEOpeY98PuCLyxupYWJ-3D3FEUgUai0a63IuPF5l9f5z0AsZLGRYNbGFHooWGMwJXhSxXDRf1PEibUsXQIp4FqXU1krBpq1Af5QKcQgDylY9TFPSxw2MCVrAHMiIQ7Jt70ybEU1HZ9ClobDqS3PCTCvcZd36EjuiSGJKPRcZPG6WwNXMUJOgmB9U3TQ1J1JI4ThnHCmjdbSeMMPjYMVU9PA8SxYImcMEkvTwpRmOSvFsJTRxUicSTYac-25Td-01QiDwhdFdz9dxzw8cZwSVWw2miBJLAyDIgA */
    id: "lonboard",

    types: {
      context: {} as {
        bboxSelectStart: number[] | undefined;
        bboxSelectEnd: number[] | undefined;
        highlightedFeature: GeoArrowPickingInfo | undefined;
      },
      events: {} as
        | {
            type: "BBox select button clicked";
          }
        | {
            type: "Map click event";
            data: PickingInfo;
          }
        | {
            type: "Map hover event";
            data: PickingInfo;
          }
        | {
            type: "Clear BBox";
          }
        | {
            type: "Cancel BBox draw";
          },
      actions: {} as
        | {
            type: "setBboxSelectStart";
          }
        | {
            type: "setBboxSelectEnd";
          }
        | {
            type: "setHighlightedFeature";
          }
        | {
            type: "clearBboxSelect";
          },
    },

    context: {
      bboxSelectStart: undefined,
      bboxSelectEnd: undefined,
      highlightedFeature: undefined,
    },

    states: {
      "Pan mode": {
        on: {
          "BBox select button clicked": {
            target: "Selecting bbox start position",
            actions: "clearBboxSelect",
          },

          "Clear BBox": {
            target: "Pan mode",
            actions: "clearBboxSelect",
          },

          "Map click event": {
            target: "Pan mode",
            actions: "setHighlightedFeature",
          },
        },
      },

      "Selecting bbox start position": {
        on: {
          "Map click event": {
            target: "Selecting bbox end position",
            actions: "setBboxSelectStart",
          },

          "Cancel BBox draw": {
            target: "Pan mode",
            reenter: true,
            actions: "clearBboxSelect",
          },
        },
      },

      "Selecting bbox end position": {
        on: {
          "Map hover event": {
            target: "Selecting bbox end position",
            actions: "setBboxSelectEnd",
          },

          "Map click event": {
            target: "Pan mode",
            actions: "setBboxSelectEnd",
          },

          "Cancel BBox draw": {
            target: "Pan mode",
            reenter: true,
            actions: "clearBboxSelect",
          },
        },
      },
    },
    initial: "Pan mode",
  },
  {
    actions: {
      clearBboxSelect: assign(() => {
        return {
          bboxSelectStart: undefined,
          bboxSelectEnd: undefined,
        };
      }),
      setBboxSelectStart: assign(({ event }) => {
        if (event.type === "Map click event" && "data" in event) {
          return {
            bboxSelectStart: event.data.coordinate,
          };
        }
        return {};
      }),
      setBboxSelectEnd: assign(({ event }) => {
        if (
          (event.type === "Map click event" ||
            event.type === "Map hover event") &&
          "data" in event
        ) {
          return {
            bboxSelectEnd: event.data.coordinate,
          };
        }
        return {};
      }),
      setHighlightedFeature: assign(({ event }) => {
        if (event.type === "Map click event" && "data" in event) {
          const clickedObject = event.data.object;

          if (typeof clickedObject !== "undefined") {
            return {
              highlightedFeature: event.data,
            };
          }
        }
        return { highlightedFeature: undefined };
      }),
    },

    actors: {},
  },
);

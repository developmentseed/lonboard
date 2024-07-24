import { assign, createMachine } from "xstate";
import { PickingInfo } from "@deck.gl/core/typed";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoB1AS2jABcACU2atHCU9KAYgBEwBjAa0KjJqAdxz1GESAG0ADAF1EoAA6pYpSqQyKQAD0QBaAEwA2AMyFTADmM2ALJYCshgIwBOGc4DsAGhABPRAcLS08HW1tjZyjLV1dLSwBfBN80LFwCQgAFHHRqAFtUSTYAIWLUHWpYMGQeGkwAV0pKDGpuZFI+aXltFTUNLSRdA0MYwhlje2dHW2cHY1djB18AhC9PMdNQ109TGQdPbZlDJJSMbHwiAGVq2pYoakxsCthKfBpe9U10NgBZHCVWu0+NQwAA3MDoSiyBSDD79dDaPQIIz7QieLwYkYyUzuJb+RA48yWGTYwwOWKzOITE4gVLnDLXGrcDSsB5PEHoCDUOFfX7-agAC1Q4LwIPBkOhPVUnwGoCRXjRrhxMk8liie1sHkMy0QMyCDhJOyizlspmM4xpdPSVxuzLubPKHK5PIwfIBbQ6vDFEKh3Vh0vhiMQXmMFk8oRiC02jmMOoQJlshHCcVMZPcMUSyVpZ2tWRy+UKYDYAGEavgHTpJf6+l8g-GLF4ZK4ZkqFkdPIYfPj46YieNPE2rIZwvtjjT0IX4IMrRcpTXZUNkaZTYQwmFZi3XA43HH9M4zGMQsurA5l6bTM5LTmLiRyDAaHQGLhmKw5zKEYMkSjzNsJiTDMO+xmrYu6hIQ7gku4zidieXhXmkN7ZLkBSSG+gafsMnaELMMRHI4y4yPYXYrM2hAhJ2sTxMScTxPB9I2kyLL3I8jovG83IBrW1bvnWRhbqutjruusTbq4ca7OsLhzOiVihDYdG5oytysixFQQs6nELi6H5ysMrjOOBxg7Nstiqh4xjat266EH+By2IYKq7MYSRJEAA */
    id: "lonboard",

    types: {
      context: {} as {
        bboxSelectStart: number[] | undefined;
        bboxSelectEnd: number[] | undefined;
      },
      events: {} as
        | {
            type: "Deck.gl was loaded";
          }
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
          },
      actions: {} as
        | {
            type: "setBboxSelectStart";
          }
        | {
            type: "setBboxSelectEnd";
          }
        | {
            type: "clearBboxSelect";
          },
    },

    context: {
      bboxSelectStart: undefined,
      bboxSelectEnd: undefined,
    },

    states: {
      "Widget is loading": {
        on: {
          "Deck.gl was loaded": {
            target: "Pan mode",
          },
        },
      },

      "Pan mode": {
        on: {
          "BBox select button clicked": "Selecting bbox start position",

          "Clear BBox": {
            target: "Pan mode",
            actions: "clearBboxSelect",
          },
        },
      },

      "Selecting bbox start position": {
        on: {
          "Map click event": {
            target: "Selecting bbox end position",
            actions: "setBboxSelectStart",
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
        },
      },
    },

    initial: "Widget is loading",
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
    },

    actors: {},
  },
);

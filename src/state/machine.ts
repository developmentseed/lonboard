import { assign, createMachine } from "xstate";
import { PickingInfo } from "@deck.gl/core/typed";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoB1AS2jABcACU2atHCU9KAYgBEwBjAa0KjJqAdxz1GESAG0ADAF1EoAA6pYpSqQyKQAD0QBaAEwA2AMyFTADmM2ALJYCshgIwBOGc4DsAGhABPRAcLS08HW1tjZyjLV1dLSwBfBN80LFwCQgAFHHRqAFtUSTYAIWLUHWpYMGQeGkwAV0pKDGpuZFI+aXltFTUNLSRdA0MYwhlje2dHW2cHY1djB18AhC9PMdNQ109TGQdPbZlDJJSMbHwiAGVq2pYoakxsCthKfBpe9U10NgBZHCVWu0+NQwAA3MDoSiyBSDD79dDaPQIIz7QieLwYkYyUzuJb+RA48yWGTYwwOWKzOITE4gVLnDLXGrcDSsB5PEHoCDUOFfX7-agAC1Q4LwIPBkOhPVUnwGoCRXjRrhxMk8liie1sHkMy0QMyCDhJOyizlspmM4xpdPSVxuzLubPKHK5PIwfIBbQ6vDFEKh3Vh0vhiMQXmMFk8oRiC02jmMOoQJlshHCcVMZPcMUSNPQhTg2itFylfS+QeRplNhDCYVmM1iDjccf0zjMYxCm1MqbM5uMlrO1pI5BgNDoDFwzFYhZlCMGSJR5m2ExJhkMtn2ZtsDdChHcJPczkMO0cXh7aQuWRy+RzE8D0+G+8IsxiR0cZZk9h8+IQrkTIX3sXixLieJj3pG0mRZe5HkdF43m5ANi39ItZSGZFDFcfUVz1Gs0PrD9dnWFw5nRKxQhsYC+0ZW5WUgioIWdOCkJdKc5WGVxnC3Ywdm2WxVQ8YxtQ-KtCAXA5bEMFVdm7JIEiAA */
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
          "BBox select button clicked": {
            target: "Selecting bbox start position",
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

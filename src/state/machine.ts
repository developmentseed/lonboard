import { assertEvent, assign, createMachine } from "xstate";

import { DeckGLRef } from "@deck.gl/react/typed";
import { PickingInfo } from "@deck.gl/core/typed";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoB1AS2jABcACU2atHCU9KAYgBEwBjAa0KjJqAdxz1GESAG0ADAF1EoAA6pYpSqQyKQAD0QBaAEwA2AMyFTADmM2ALJYCshgIwBOGc4DsAGhABPRAcLS08HW1tjZyjLV1dLSwBfBN80LFwCQgAFHHRqAFtUSTYAIWLUHWpYMGQeGkwAV0pKDGpuZFI+aXltFTUNLSRdA0MYwhlje2dHW2cHY1djB18AhC9PMdNQ109TGQdPbZlDJJSMbHwiAGVq2pYoakxsCthKfBpe9U10NgBZHCVWu0+NQwAA3MDoSiyBSDD79dDaPQIIz7QieLwYkYyUzuJb+RA48yWGTYwwOWKzOITE4gVLnDLXGrcDSsB5PEHoCDUOFfX7-QEdXgg8GQ6E9VSfAagJFeYwWTyhGILTaOYzLRAmWyEcJxUxk9wxRI09CFODaOnpCDivpfREGUy2cxhMKzGaxBxudXI5xmMYhTamPVmYzjGkWi4kcgwGh0Bi4Zisa2ShGDJEo8zbCYkwyGWz7UwTL36UKEdwk9zOQw7RxeMNnS1ZHL5U1J+F25E59azGJHRwOmT2Hz4hCuLUhKuxeLEuLxOtpCOM26sx7lSqvPDvCVt2Fb22p4auILOmYu92e4e7dYuOboqyhGxz+lXG7Mu5s1cQrk8qUgb8p6UHs4pbGDs2y2J4xI+oYXouoQWYHLYhgyDsoZJAkQA */
    id: "lonboard",

    types: {
      context: {} as {
        bboxSelectStart: number[] | undefined;
        bboxSelectStartPixel: number[] | undefined;
        bboxSelectEnd: number[] | undefined;
        bboxSelectEndPixel: number[] | undefined;
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
      bboxSelectEndPixel: undefined,
      bboxSelectEnd: undefined,
      bboxSelectStartPixel: undefined,
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
        // assertEvent(event, "Map click event");
        console.log(event.data);
        return {
          bboxSelectStart: event.data.coordinate,
        };
      }),
      setBboxSelectEnd: assign(({ event }) => {
        // assertEvent(event, "Map click event");
        return {
          bboxSelectEnd: event.data.coordinate,
        };
      }),
    },

    actors: {},
  },
);

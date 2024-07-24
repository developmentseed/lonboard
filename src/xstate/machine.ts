import { assign, createMachine } from "xstate";
import { PickingInfo } from "@deck.gl/core/typed";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoB1AS2jABcACU2atHCU9KAYgBEwBjAa0KjJqAdxz1GESAG0ADAF1EoAA6pYpSqQyKQAD0QBaAEwA2AJyEALAGYA7AA47M+7ZsBWGVYA0IAJ4HTNoSmAIxWpiE2Hq6GMoZ2AL7x3mhYuASEAAo46NQAtqiSbABCRag61LBgyDw0mACulJQY1NzIpHzS8toqahpaSLoGceYyxhZ2wXauFsGuZsau3n4IwTaBHm4BVjKuNgGxickY2PhEWTn5hQDC1fjUJWWyCgM96pro2noIdoaEhqsycaGPamWJTJYGYyEYIBWY2UJmCy7caHEApE7pADKVRqLCg1Ew2HKsEo+Borz66DYAFkcEoWm0+NQwAA3MDoShPbqqN79UBfIy7QjwkXBOIeUGLXyIMJWQiODyGVzhWamOxjVHotJEbHVbgaVgEonM9AQagU940unUAAWqDZeGZbI5XJePMpn0Qq2FpjCTgmwR2FhkYohCBmrkI7icVmCcesxlGmuO2sIutxhsJZRNZotGCt9Na7V4TvZnK6bt6709KxsUJcrjs4WMtimxjDJgslgsaqsStBTYSSTRKdOaZx+rxRuzJLJ5vdlqu2W4VXupXKEDwOGEruUC75gwQ+kD0NMFgse2Mqx+djW7elKybf1ccxsJjM0SbVkSw-QBTg2haqc3JVgeApWNYUZIhGMzhK4MJhvo2zBJYYrBNYcTBu4NjJqkY5kBQNB0AwuDMKwIG8h8AwCiYMiELEdbbO4sxInMiH-F2hiGOMypuCGdisbhGJnNkeT-hRHrUUMwLQo2oJxK4EGAreYZnvKb4gg4jhqg4Qmpumk6Zsas54OS+5UXuoEWYeRimJG0zTCxMJ2QhD7bIE-yvqEt5zMYeljgZBr4lm5Tsrm5kSdWUlHoYIRBMYNhhDYF6OMExiGGGjmEGMThnjEiVJj+QA */
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

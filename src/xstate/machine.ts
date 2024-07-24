import { assign, createMachine } from "xstate";
import { PickingInfo } from "@deck.gl/core/typed";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoB1AS2jABcACU2atHCU9KAYgBEwBjAa0KjJqAdxz1GESAG0ADAF1EoAA6pYpSqQyKQAD0QBaAEwA2AJyEALAGYA7AA47M+7ZsBWGVYA0IAJ4HTNoSmAIxWpiE2Hq6GMoZ2AL7x3mhYuASEAAo46NQAtqiSbABCRag61LBgyDw0mACulJQY1NzIpHzS8toqahpaSLoGceYyxhZ2wXauFsGuZsau3n4IwTaBHm4BVjKuNgGxickY2PhEWTn5hQDC1fjUJWWyCgM96pro2noIdoaEhqsycaGPamWJTJYGYyEYIBWY2UJmCy7caHEApE7pADKVRqLCg1Ew2HKsEo+Borz66DYAFkcEoWm0+NQwAA3MDoShPbqqN79UBfIy7QjwkXBOIeUGLXyIMJWQiODyGVzhWamOxjVHotJEbHVbgaVgEonM9AQagU940unUAAWqDZeGZbI5XJePMpn0Qq2FpjCTgmwR2FhkYohCBmrkI7icVmCcesxlGmuO2sIutxhsJZRNZotGCt9Na7V4TvZnK6bt6709KxsUJcrjs4WMtimxjDJgslgsaqsStBTYSSTRKdOaZx+rxRuzJLJ5vdlqu2W4VXupXKEDwOGEruUC75gwQ+nGXasfcDY1jxhsVjsHeBUeikwscWMhjV1mTqTH6cnmeN7K5vuVJLugK5CA8G5bjuFZ7lWB4Co2cqmNe17BrESI9mG0yBIYwKNrEZ6Jk4iTDugBRwNoWqnNy8EfAMAotsEQSoTY6GGJhphhvo2zMTM-zBpEIb2F+GJEGQFA0HQDC4MwrC0by9H8kMiaELEdbbO4sxInM3ECX8HFTAEWl2DpompuceQUQpHoMUMD6zE2YKuFYwbjDYYamF2dg2MC4QOI4aoOOZP4Tga+JZsSpJ4OSwE2dWdlHu+kbTNM2kwqYrgwmG2y4bM16hD5czGCFWJhVOkU5vOdHxQhQwhCxN7+UhkoWNhMzQlEcw-LY2ymKR8RAA */
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

          "Cancel BBox draw": {
            target: "Pan mode",
            reenter: true,
            actions: "clearBboxSelect",
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

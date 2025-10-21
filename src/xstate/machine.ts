import { PickingInfo } from "@deck.gl/core";
import { GeoArrowPickingInfo } from "@geoarrow/deck.gl-layers";
import { assign, createMachine } from "xstate";

export const machine = createMachine(
  {
    /** @xstate-layout N4IgpgJg5mDOIC5QBsD2A7ARqghgJwgDoAFHdAAgFtUIwBiAIQdQA9zYxkwBjAF3MwBXXrwzluyAJbcA1pADaABgC6iUAAdUsSb0kY1IFogC0AJgAcATkKKAbABZzARnMBWe09e3Lt1wBoQAE9EJwB2UJsAZlDXS1DIxVdQuMVTAF80gLQsXAISMioaegBhLnxyJlYlVSQQTW1dfVqjBHNTQlMwxUdTZMtUtwDghGNbQic4z1CnSO97JMcMrIxsfCJSCmpaOgBZHHVxKVlyMAA3MHReaoN6nT10AxbjJ1Mx0PtIyPtLT98Z0yGJl69hsL1moUU5g+tjsSxA2VWeQ2hW2pS0YHYklo5HUZE411qt0aD2aJlckSc43spm+lnMthp0UigJGpgphCsrk8-Wm5I+cIRuSIAGVODxdOgoAJsGxYLx8PwifddvtDtIZCdzpcCRotHcmqAnqYkoRpmaXuZFJF+v4gohrZEOYorcbLJZufT7AKVkLCKKuHxJJLpax2PK8Iq9cS6MUyNxOBVmGwIHgcAB3HV1KP3R4mRwgz6dOwfJy2eLmFmmXqEVyuTpQiwMun8zLwn1rP1iwPBzAyk7oCA47MYFUHAAWqHOeE1FyuKhuw5JhpC7WdsRpTns8VLENtwx6hEibNCbOp9lS9l83pyHf94qDUt7oYug6VI72Bwk6pn2vnhMXuYIGEYzRDEVg+NEbi2JWDiEPY3zmEesSQnS16IiKXYSo+fYvkODTKrG6Dxsgiahim6aZm+S6GGSiGED4oRlueF7uJYLLuBEVZgakvzOqEaG+ne3bYaGcoKnh+roDGaAcJi2K4ug+J-rq+EGjRrLmByrjmOE9KmIoLihIMdoIJEtY1nxFJOJusywq2gq3phD4hmwuFUdJ6JyRiClKTUKmSYBzzaRy5YxJe5LRPMLKMdYsxQjpfFbuYGStugRTwLUDkEAuqnUU8tjsgxTHOjSrEssYsyUhMEHJC8SWuAJHbIlsYA5QFpKstWnhWHY7zdEkMTlXS4yeN0tgMjpnQTI1eRCVhLlhuJVFtcSgWmJYrg1vMHjuNVXJsSZCScZ4ZYzDpXi2DNGEBvNT6uQOEmrf+uVre69HFVYHyKG6lj2CytguIeP1cvE2kxJdKVAA */
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
          }
        | {
            type: "Close side panel";
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
          }
        | {
            type: "clearHighlightedFeature";
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

          "Close side panel": {
            target: "Pan mode",
            actions: "clearHighlightedFeature",
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

          "Close side panel": {
            target: "Selecting bbox start position",
            actions: "clearHighlightedFeature",
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

          "Close side panel": {
            target: "Selecting bbox end position",
            actions: "clearHighlightedFeature",
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
      clearHighlightedFeature: assign(() => {
        return { highlightedFeature: undefined };
      }),
    },

    actors: {},
  },
);

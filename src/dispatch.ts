import { AnyModel } from "@anywidget/types";
import { v4 } from "uuid";

type Message<T> = {
  id: string;
  kind: "anywidget-dispatch-response";
  response: T;
};

type GetTileDataAction = {
  type: "get-tile-data";
  data: {
    x: number;
    y: number;
    z: number;
  };
};

type Action = GetTileDataAction;

export function dispatch<T>(
  model: AnyModel,
  action: Action,
  { timeout = 3000 } = {},
) {
  let id = v4();
  return new Promise((resolve, reject) => {
    let timer = setTimeout(() => {
      reject(new Error(`Promise timed out after ${timeout} ms`));
      model.off("msg:custom", handler);
    }, timeout);

    function handler(msg: Message<T>, buffers: DataView[]) {
      if (!(msg.id === id)) return;
      clearTimeout(timer);
      resolve([msg.response, buffers]);
      model.off("msg:custom", handler);
    }
    model.on("msg:custom", handler);
    model.send({ id, kind: "anywidget-dispatch", action });
  });
}

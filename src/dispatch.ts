import { AnyModel } from "@anywidget/types";

type Message<T> = {
  id: string;
  kind: "anywidget-dispatch-response";
  response: T;
};

export function dispatch<T>(
  model: AnyModel,
  action: any,
  { timeout = 3000 } = {},
) {
  let id = Date.now().toString(36);
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
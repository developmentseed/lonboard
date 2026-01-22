// Invoke is vendored from anywidget because we want to ensure we're using the
// widget messages on the **specific** widget layer, not the top-level Map
// layer. E.g. when the JS BitmapTileLayer is requesting tiles, we want to make
// sure that the same, specific BitmapTileLayer on the Python side is receiving
// the requests.
//
// For now, it's simplest to vendor this code and implement our own responses on
// the Python side.
//
// https://github.com/manzt/anywidget/blob/41a1aff623e844efb62cc4bb706c58b2dc3b32b1/packages/anywidget/src/widget.js#L267-L306

import type { AnyModel } from "@anywidget/types";
import * as uuid from "uuid";

type InvokeOptions = {
  buffers?: DataView[];
  signal?: AbortSignal;
};

export async function invoke<T>(
  model: AnyModel,
  msg: object,
  options: InvokeOptions = {},
): Promise<[T, DataView[]]> {
  // crypto.randomUUID() is not available in non-secure contexts (i.e., http://)
  // so we use simple (non-secure) polyfill.
  const id = uuid.v4();
  const signal = options.signal ?? AbortSignal.timeout(3000);

  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      console.log("signal already aborted");
      reject(signal.reason);
    }
    signal.addEventListener("abort", () => {
      console.log("aborting from signal again");
      model.off("msg:custom", handler);
      reject(signal.reason);
    });

    function handler(
      msg: { id: string; kind: "anywidget-command-response"; response: T },
      buffers: DataView[],
    ) {
      if (!(msg.id === id)) return;
      resolve([msg.response, buffers]);
      model.off("msg:custom", handler);
    }
    model.on("msg:custom", handler);
    model.send(
      { id, kind: "anywidget-command", msg },
      undefined,
      options.buffers ?? [],
    );
  });
}

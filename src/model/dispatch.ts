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

import type { WidgetModel } from "@jupyter-widgets/base";
import type { JSONValue } from "@lumino/coreutils";
import * as uuid from "uuid";

type InvokeOptions = {
  buffers?: DataView[];
  signal?: AbortSignal;
  timeout?: number;
};

export async function invoke<ResponseT>(
  model: WidgetModel,
  msg: JSONValue,
  kind: string = "lonboard-command",
  options: InvokeOptions = {},
): Promise<[ResponseT, DataView[]]> {
  // crypto.randomUUID() is not available in non-secure contexts (i.e., http://)
  // so we use simple (non-secure) polyfill.

  // We need a stable ID per invocation because we'll have many concurrent tile
  // fetches.
  const id = uuid.v4();

  const { signal } = options;
  // Default 5-second timeout for callers that don't pass one.
  const timeout = options.timeout ?? 5000;

  // Return a promise that resolves when we get a response message with the
  // correct ID, or rejects if the signal is aborted or the timeout passes.
  return new Promise((resolve, reject) => {
    // We need to track whether we've already resolved/rejected to avoid
    // multiple calls to resolve/reject.
    let settled = false;

    if (signal?.aborted) {
      reject(signal.reason);
      return;
    }

    // Stop waiting for a response, then tell Python to drop the request.
    const cancel = (reason: unknown) => {
      if (settled) {
        return;
      }
      settled = true;

      cleanup();
      reject(reason);
      try {
        model.send({ id, kind: `${kind}-cancel` });
      } catch (error) {
        // The comm is gone (e.g. the kernel restarted), so Python has no
        // request left to cancel.
        console.warn(`Could not cancel ${kind} request:`, error);
      }
    };

    const abortHandler = () => cancel(signal?.reason);

    // A timer rather than `AbortSignal.timeout`, so that the timeout also
    // applies when the caller passes a signal (deck.gl aborts a tile's signal
    // only once it no longer needs that tile), and so that nothing outlives the
    // request once Python responds.
    const timer = setTimeout(() => {
      cancel(
        new DOMException(
          `No response to ${kind} within ${timeout} ms`,
          "TimeoutError",
        ),
      );
    }, timeout);

    function cleanup() {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abortHandler);
      model.off("msg:custom", handler);
    }

    signal?.addEventListener("abort", abortHandler);

    function handler(
      msg: { id: string; kind: `${string}-response`; response: ResponseT },
      buffers: DataView[],
    ) {
      // ID mismatches are expected because we have many concurrent invocations.
      if (!(msg.id === id)) {
        return;
      }

      if (settled) {
        return;
      }
      settled = true;

      cleanup();
      resolve([msg.response, buffers]);
    }

    model.on("msg:custom", handler);
    try {
      model.send({ id, kind, msg }, undefined, options.buffers ?? []);
    } catch (error) {
      settled = true;
      cleanup();
      reject(error);
    }
  });
}

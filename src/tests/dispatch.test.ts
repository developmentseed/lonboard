import { afterEach, describe, expect, it, vi } from "vitest";

import { invoke } from "../model/dispatch.js";
import { FakeWidgetModel } from "./fake-widget-model.js";

const KIND = "raster-get-tile-data";

type Settled =
  | { status: "fulfilled"; value: unknown }
  | { status: "rejected"; reason: unknown }
  | { status: "pending" };

/**
 * Wait up to `ms` for `promise` to settle.
 *
 * A promise that is still pending after `ms` is reported as pending, so that a
 * request that hangs fails its test instead of hanging it.
 */
async function settleWithin(
  promise: Promise<unknown>,
  ms: number,
): Promise<Settled> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const pending = new Promise<Settled>((resolve) => {
    timer = setTimeout(() => resolve({ status: "pending" }), ms);
  });

  try {
    return await Promise.race([
      promise.then(
        (value): Settled => ({ status: "fulfilled", value }),
        (reason): Settled => ({ status: "rejected", reason }),
      ),
      pending,
    ]);
  } finally {
    clearTimeout(timer);
  }
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe("invoke without a signal", () => {
  it("times out when Python never replies", async () => {
    const model = new FakeWidgetModel({});

    const result = await settleWithin(
      invoke(model.asWidgetModel(), {}, KIND, { timeout: 50 }),
      1000,
    );

    expect(result).toMatchObject({
      status: "rejected",
      reason: { name: "TimeoutError" },
    });
  });
});

describe("invoke with a signal", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("times out when Python never replies and the signal never aborts", async () => {
    const model = new FakeWidgetModel({});
    const { signal } = new AbortController();

    const result = await settleWithin(
      invoke(model.asWidgetModel(), {}, KIND, { signal, timeout: 50 }),
      1000,
    );

    expect(result).toMatchObject({
      status: "rejected",
      reason: {
        name: "TimeoutError",
        message: `No response to ${KIND} within 50 ms`,
      },
    });
  });

  it("tells Python to cancel a request that timed out", async () => {
    const model = new FakeWidgetModel({});
    const { signal } = new AbortController();

    await settleWithin(
      invoke(model.asWidgetModel(), {}, KIND, { signal, timeout: 50 }),
      1000,
    );

    const [request, ...rest] = model.sent;
    expect(rest).toEqual([{ id: request.id, kind: `${KIND}-cancel` }]);
  });

  it("rejects with the abort reason when the signal aborts", async () => {
    const model = new FakeWidgetModel({});
    const controller = new AbortController();

    const promise = invoke(model.asWidgetModel(), {}, KIND, {
      signal: controller.signal,
      timeout: 10000,
    });
    controller.abort();

    expect(await settleWithin(promise, 1000)).toMatchObject({
      status: "rejected",
      reason: { name: "AbortError" },
    });
    const [request, ...rest] = model.sent;
    expect(rest).toEqual([{ id: request.id, kind: `${KIND}-cancel` }]);
  });

  it("rejects without sending anything when the signal has already aborted", async () => {
    const model = new FakeWidgetModel({});
    const controller = new AbortController();
    controller.abort();

    const result = await settleWithin(
      invoke(model.asWidgetModel(), {}, KIND, {
        signal: controller.signal,
        timeout: 10000,
      }),
      1000,
    );

    expect(result).toMatchObject({
      status: "rejected",
      reason: { name: "AbortError" },
    });
    expect(model.sent).toEqual([]);
  });

  it("resolves with the response and does not cancel it after the timeout", async () => {
    const model = new FakeWidgetModel({});
    const { signal } = new AbortController();

    const promise = invoke(model.asWidgetModel(), {}, KIND, {
      signal,
      timeout: 50,
    });
    const [request] = model.sent;
    model.receive({ id: request.id, kind: `${KIND}-response`, response: 1 });

    expect(await promise).toEqual([1, []]);
    await wait(100);
    expect(model.sent).toEqual([request]);
  });

  it("lets go of the signal and the timer once Python responds", async () => {
    vi.useFakeTimers();
    const model = new FakeWidgetModel({});
    const { signal } = new AbortController();
    const addListener = vi.spyOn(signal, "addEventListener");
    const removeListener = vi.spyOn(signal, "removeEventListener");

    const promise = invoke(model.asWidgetModel(), {}, KIND, {
      signal,
      timeout: 60000,
    });
    const [request] = model.sent;
    model.receive({ id: request.id, kind: `${KIND}-response`, response: 1 });
    await promise;

    // deck.gl keeps a tile's signal for as long as it caches the tile, so a
    // listener left on it would keep the response's buffers alive as well.
    expect(addListener).toHaveBeenCalledTimes(1);
    const [[type, listener]] = addListener.mock.calls;
    expect(removeListener).toHaveBeenCalledWith(type, listener);
    expect(vi.getTimerCount()).toBe(0);
  });
});

// JupyterLab's comm throws on send once the kernel has restarted or died.
describe("invoke when the comm can't send", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  function breakComm(model: FakeWidgetModel) {
    return vi.spyOn(model, "send").mockImplementation(() => {
      throw new Error("Cannot send");
    });
  }

  it("rejects right away and later sends nothing when the request can't be sent", async () => {
    vi.useFakeTimers();
    const model = new FakeWidgetModel({});
    const send = breakComm(model);
    const controller = new AbortController();

    await expect(
      invoke(model.asWidgetModel(), {}, KIND, {
        signal: controller.signal,
        timeout: 50,
      }),
    ).rejects.toThrow("Cannot send");

    await vi.advanceTimersByTimeAsync(50);
    controller.abort();
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("still rejects when the signal aborts and the cancel can't be sent", async () => {
    const model = new FakeWidgetModel({});
    const controller = new AbortController();
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    const promise = invoke(model.asWidgetModel(), {}, KIND, {
      signal: controller.signal,
      timeout: 10000,
    });
    breakComm(model);
    controller.abort();

    expect(await settleWithin(promise, 1000)).toMatchObject({
      status: "rejected",
      reason: { name: "AbortError" },
    });
    expect(warn).toHaveBeenCalledOnce();
  });
});

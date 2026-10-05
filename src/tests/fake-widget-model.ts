import type { WidgetModel } from "@jupyter-widgets/base";

type Listener = (...args: any[]) => void;

/**
 * A minimal stand-in for a Jupyter `WidgetModel`.
 *
 * It follows the event semantics of the Backbone model that `WidgetModel` is
 * built on: `set` fires `change:<name>` and then `change`, and `off` without a
 * callback removes every listener for that event.
 *
 * Custom messages that JS sends to Python are recorded in `sent`, and nothing
 * replies to them unless a test calls `receive`.
 */
export class FakeWidgetModel {
  widget_manager: { get_model: (modelId: string) => Promise<WidgetModel> };

  /** Custom messages sent to the Python side, in order. */
  sent: Record<string, unknown>[] = [];

  private state: Record<string, unknown>;
  private listeners: Map<string, Listener[]> = new Map();

  /**
   * @param state     Initial state of the model.
   * @param children  Other models that this model's widget manager can load, keyed by model id.
   */
  constructor(
    state: Record<string, unknown>,
    children: Record<string, FakeWidgetModel> = {},
  ) {
    this.state = { ...state };
    this.widget_manager = {
      get_model: async (modelId) => children[modelId].asWidgetModel(),
    };
  }

  get(name: string): unknown {
    return this.state[name];
  }

  set(name: string, value: unknown): void {
    this.state[name] = value;
    this.trigger(`change:${name}`);
    this.trigger("change");
  }

  on(event: string, callback: Listener): void {
    this.listeners.set(event, [...(this.listeners.get(event) ?? []), callback]);
  }

  off(event: string, callback?: Listener): void {
    const remaining = callback
      ? (this.listeners.get(event) ?? []).filter((l) => l !== callback)
      : [];
    this.listeners.set(event, remaining);
  }

  send(content: Record<string, unknown>): void {
    this.sent.push(content);
  }

  /** Deliver a custom message from the Python side. */
  receive(content: Record<string, unknown>, buffers: DataView[] = []): void {
    this.trigger("msg:custom", content, buffers);
  }

  asWidgetModel(): WidgetModel {
    return this as unknown as WidgetModel;
  }

  private trigger(event: string, ...args: unknown[]): void {
    for (const listener of this.listeners.get(event) ?? []) {
      listener(...args);
    }
  }
}

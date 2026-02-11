/**
 * State management for Lonboard.
 *
 * Two types of state:
 * - Client-only: UI state that never syncs with Python (Zustand). See `store.ts`
 * - Python-synced: State that bidirectionally syncs with Python (Backbone). See `python-sync.ts`
 */

export { useViewStateDebounced } from "./python-sync.js";
export { useStore } from "./store.js";

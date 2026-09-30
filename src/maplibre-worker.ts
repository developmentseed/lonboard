import { setWorkerUrl } from "maplibre-gl";

// Injected by build.mjs
declare const MAPLIBRE_WORKER_SOURCE: string;

/**
 * Point maplibre-gl at its worker.
 *
 * maplibre-gl ships its worker as a separate file and expects to load it from a
 * URL. We ship a single file, so the worker is bundled into a string at build
 * time and started from a Blob URL.
 */
export function initMaplibreWorker() {
  const blob = new Blob([MAPLIBRE_WORKER_SOURCE], { type: "text/javascript" });
  // maplibre-gl starts a classic worker when the URL ends in ".cjs", and a
  // module worker otherwise. Browsers refuse to start a module worker from a
  // Blob URL on a `file://` page, such as an HTML export opened from disk.
  setWorkerUrl(`${URL.createObjectURL(blob)}#.cjs`);
}

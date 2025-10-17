// @ts-expect-error: Cannot find module '@geoarrow/geoarrow-js/earcut.worker.min.js' or its corresponding type declarations.
// This is fine because we're only loading this as text to create a worker
import earcutWorkerText from "@geoarrow/geoarrow-js/earcut.worker.min.js";
import type { FunctionThread } from "threads";
import { spawn, BlobWorker, Pool } from "threads";

async function createEarcutPool(
  earcutWorkerPoolSize: number,
): Promise<Pool<FunctionThread>> {
  return Pool<FunctionThread>(
    () => spawn(BlobWorker.fromText(earcutWorkerText)),
    earcutWorkerPoolSize,
  );
}

/**
 * The PolygonLayer and SolidPolygonLayer perform [Earcut][earcut] triangulation on worker threads.
 *
 * Previously, in deck.gl-layers v0.3, there was an earcut worker pool created
 * internally per GeoArrowPolygonLayer or GeoArrowSolidPolygonLayer. This wasn't
 * ideal, because if you had multiple polygon layers, you'd end up with multiple
 * earcut worker pools competing for resources. But it wasn't _that_ bad because
 * each GeoArrow layer rendered all batches within a table.
 *
 * In the deck.gl-layers upgrade to v0.4, there's now only deck.gl layer call per _record batch_, not per _table_. That means by default we'd be creating a new earcut worker pool for **every record batch**.
 *
 * Instead, we now create a single top-level earcut worker pool that is shared across all GeoArrow polygon layers.
 *
 * [earcut]: https://github.com/mapbox/earcut
 */
export const earcutWorkerPool = await createEarcutPool(8);

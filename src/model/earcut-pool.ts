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

export const earcutWorkerPool = await createEarcutPool(8);

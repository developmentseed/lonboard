import _initParquetWasm, { readParquet } from "parquet-wasm";
import * as arrow from "apache-arrow";

// NOTE: this version must be synced exactly with the parquet-wasm version in
// use.
const PARQUET_WASM_VERSION = "0.6.1";
const PARQUET_WASM_CDN_URL = `https://cdn.jsdelivr.net/npm/parquet-wasm@${PARQUET_WASM_VERSION}/esm/parquet_wasm_bg.wasm`;
let WASM_READY: boolean = false;

export async function initParquetWasm() {
  if (WASM_READY) {
    return;
  }

  await _initParquetWasm(PARQUET_WASM_CDN_URL);
  WASM_READY = true;
}

/**
 * Parse a Parquet buffer to an Arrow JS table
 */
export function parseParquet(dataView: DataView): arrow.Table {
  if (!WASM_READY) {
    throw new Error("wasm not ready");
  }

  console.time("readParquet");

  // TODO: use arrow-js-ffi for more memory-efficient wasm --> js transfer?
  const arrowIPCBuffer = readParquet(new Uint8Array(dataView.buffer), {
    batchSize: Math.pow(2, 31),
  }).intoIPCStream();
  const arrowTable = arrow.tableFromIPC(arrowIPCBuffer);

  console.timeEnd("readParquet");

  return arrowTable;
}

/**
 * Parse a list of buffers containing Parquet chunks into an Arrow JS table
 *
 * Each buffer in the list is expected to be a fully self-contained Parquet file
 * that can parse on its own and consists of one arrow Record Batch
 *
 * @var {[type]}
 */
export function parseParquetBuffers(dataViews: DataView[]): arrow.Table {
  const batches: arrow.RecordBatch[] = [];
  for (const chunkBuffer of dataViews) {
    const table = parseParquet(chunkBuffer);
    if (table.batches.length !== 1) {
      console.warn("Expected one batch");
    }
    batches.push(...table.batches);
  }

  return new arrow.Table(batches);
}

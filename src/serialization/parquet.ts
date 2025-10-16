import * as arrow from "apache-arrow";
import _initParquetWasm, { readParquet } from "parquet-wasm";
import {} from "parquet-wasm";

// NOTE: this version must be synced exactly with the parquet-wasm version in
// use.
const PARQUET_WASM_VERSION = "0.7.1";
const PARQUET_WASM_CDN_URL = `https://cdn.jsdelivr.net/npm/parquet-wasm@${PARQUET_WASM_VERSION}/esm/parquet_wasm_bg.wasm`;
let WASM_READY: boolean = false;

// We initiate the fetch immediately (but don't await it) so that it can be
// downloaded in the background on app start
const PARQUET_WASM_FETCH = fetch(PARQUET_WASM_CDN_URL);

const PARQUET_MAGIC = new TextEncoder().encode("PAR1");

/** Initialize the parquet-wasm WASM buffer */
export async function initParquetWasm() {
  if (WASM_READY) {
    return;
  }

  const wasm_buffer = await PARQUET_WASM_FETCH;
  await _initParquetWasm(wasm_buffer);
  WASM_READY = true;
  return;
}

// For now, simplest to just ensure this is called at least once on module load
await initParquetWasm();

export function isParquetBuffer(dataView: DataView): boolean {
  if (dataView.byteLength < PARQUET_MAGIC.length) {
    return false;
  }

  for (let i = 0; i < PARQUET_MAGIC.length; i++) {
    if (dataView.getUint8(i) !== PARQUET_MAGIC[i]) {
      return false;
    }
  }

  return true;
}

/**
 * Parse a Parquet buffer to an Arrow JS table
 */
export function parseParquet(dataView: DataView): arrow.Table {
  console.time("readParquet");

  // TODO: use arrow-js-ffi for more memory-efficient wasm --> js transfer?
  const arrowIPCBuffer = readParquet(new Uint8Array(dataView.buffer), {
    batchSize: Math.pow(2, 31),
  }).intoIPCStream();
  const arrowTable = arrow.tableFromIPC(arrowIPCBuffer);

  console.timeEnd("readParquet");

  return arrowTable;
}

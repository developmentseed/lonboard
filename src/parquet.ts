import { useEffect, useState } from "react";
import { initSync, readParquet } from "parquet-wasm/esm/arrow2";
import * as arrow from "apache-arrow";

let WASM_READY: boolean = false;

// https://developer.mozilla.org/en-US/docs/Web/API/Compression_Streams_API
async function decompressBlob(blob: Blob) {
  const ds = new DecompressionStream("gzip");
  const decompressedStream = blob.stream().pipeThrough(ds);
  return await new Response(decompressedStream).blob();
}

/**
 * Initialize parquet-wasm from an existing WASM binary blob.
 * It is expected that this WASM has been gzipped
 *
 * @return Whether initialization succeeded
 */
export async function initParquetWasmFromBinary(
  view: DataView | null,
): Promise<boolean> {
  if (!view) {
    return false;
  }

  let blob = new Blob([view]);
  const decompressedBlob = await decompressBlob(blob);
  const decompressedBuffer = await decompressedBlob.arrayBuffer();

  initSync(decompressedBuffer);
  WASM_READY = true;
  return true;
}

/**
 * Parse a Parquet buffer to an Arrow JS table
 */
export function parseParquet(dataView: DataView): arrow.Table {
  if (!WASM_READY) {
    throw new Error("wasm not ready");
  }

  console.time("readParquet");

  // TODO: use arrow-js-ffi for more memory-efficient wasm --> js transfer
  const arrowIPCBuffer = readParquet(
    new Uint8Array(dataView.buffer),
  ).intoIPCStream();
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

export function useParquetWasm(view: DataView | null): [boolean] {
  const [wasmReady, setWasmReady] = useState<boolean>(false);

  // Init parquet wasm
  useEffect(() => {
    const callback = async () => {
      const succeeded = await initParquetWasmFromBinary(view);
      if (succeeded) {
        setWasmReady(true);
      }
    };

    callback();
  }, []);

  return [wasmReady];
}

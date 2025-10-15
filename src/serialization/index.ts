import * as arrow from "apache-arrow";

import { parseArrowIPC } from "./ipc";
import { isParquetBuffer, parseParquet } from "./parquet";

/**
 * Parse a list of buffers containing either Parquet or Arrow IPC chunks into an
 * Arrow JS table
 *
 * Each buffer in the list is expected to be a fully self-contained Parquet file
 * or Arrow IPC file/stream that can parse on its own and consists of one arrow
 * Record Batch
 */
export function deserializeArrowTable(dataViews: DataView[]): arrow.Table {
  const batches: arrow.RecordBatch[] = [];
  for (const chunkBuffer of dataViews) {
    let table: arrow.Table;

    if (isParquetBuffer(chunkBuffer)) {
      table = parseParquet(chunkBuffer);
    } else {
      // Assume Arrow IPC
      table = parseArrowIPC(chunkBuffer);
    }

    if (table.batches.length !== 1) {
      console.warn(`Expected one batch in table, got ${table.batches.length}`);
    }

    batches.push(...table.batches);
  }

  return new arrow.Table(batches);
}

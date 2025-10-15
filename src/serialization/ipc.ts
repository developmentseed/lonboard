import * as arrow from "apache-arrow";
import * as lz4 from "lz4js";

const lz4Codec: arrow.Codec = {
  encode(data: Uint8Array): Uint8Array {
    return lz4.compress(data);
  },
  decode(data: Uint8Array): Uint8Array {
    return lz4.decompress(data);
  },
};

let LZ4_CODEC_SET: boolean = false;

/**
 * Parse an Arrow IPC buffer to an Arrow JS table
 */
export function parseArrowIPC(dataView: DataView): arrow.Table {
  if (!LZ4_CODEC_SET) {
    arrow.compressionRegistry.set(arrow.CompressionType.LZ4_FRAME, lz4Codec);
    LZ4_CODEC_SET = true;
  }

  console.time("readArrowIPC");
  const arrowTable = arrow.tableFromIPC(dataView);
  console.timeEnd("readArrowIPC");
  return arrowTable;
}

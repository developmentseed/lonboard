import * as arrow from "apache-arrow";
import { parseParquetBuffers } from "./parquet";
import { useState, useEffect } from "react";

export function useTableBufferState(
  wasmReady: boolean,
  dataRaw: DataView[]
): [arrow.Table | null] {
  const [dataTable, setDataTable] = useState<arrow.Table | null>(null);
  // Only parse the parquet buffer when the data itself or wasmReady has changed
  useEffect(() => {
    const callback = () => {
      if (wasmReady && dataRaw && dataRaw.length > 0) {
        console.log(
          `table byte lengths: ${dataRaw.map(
            (dataView) => dataView.byteLength
          )}`
        );

        setDataTable(parseParquetBuffers(dataRaw));
      }
    };
    callback();
  }, [wasmReady, dataRaw]);

  return [dataTable];
}

export function useAccessorState(wasmReady: boolean, accessorRaw: any): any {
  const [accessorValue, setAccessorValue] = useState(null);

  // Only parse the parquet buffer when the data itself or wasmReady has changed
  useEffect(() => {
    const callback = () => {
      setAccessorValue(
        accessorRaw instanceof Array && accessorRaw?.[0] instanceof DataView
          ? wasmReady && accessorRaw?.[0].byteLength > 0
            ? parseParquetBuffers(accessorRaw).getChildAt(0)
            : null
          : accessorRaw
      );
    };
    callback();
  }, [wasmReady, accessorRaw]);

  return [accessorValue];
}

export function parseAccessor(accessorRaw: unknown): any {
  return accessorRaw instanceof Array && accessorRaw?.[0] instanceof DataView
    ? accessorRaw?.[0].byteLength > 0
      ? parseParquetBuffers(accessorRaw).getChildAt(0)
      : null
    : accessorRaw;
}

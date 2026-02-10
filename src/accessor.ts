import type * as arrow from "apache-arrow";
import { useEffect, useState } from "react";

import { parseParquetBuffers } from "./parquet.js";

type AccessorRaw = DataView[] | unknown;

export function useTableBufferState(
  wasmReady: boolean,
  dataRaw: DataView[],
): [arrow.Table | null] {
  const [dataTable, setDataTable] = useState<arrow.Table | null>(null);
  // Only parse the parquet buffer when the data itself or wasmReady has changed
  useEffect(() => {
    const callback = () => {
      if (wasmReady && dataRaw && dataRaw.length > 0) {
        console.log(
          `table byte lengths: ${dataRaw.map(
            (dataView) => dataView.byteLength,
          )}`,
        );

        setDataTable(parseParquetBuffers(dataRaw));
      }
    };
    callback();
  }, [wasmReady, dataRaw]);

  return [dataTable];
}

export function useAccessorState(
  wasmReady: boolean,
  accessorRaw: AccessorRaw,
): [arrow.Vector | null] {
  const [accessorValue, setAccessorValue] = useState<arrow.Vector | null>(null);

  // Only parse the parquet buffer when the data itself or wasmReady has changed
  useEffect(() => {
    const callback = () => {
      setAccessorValue(
        Array.isArray(accessorRaw) && accessorRaw?.[0] instanceof DataView
          ? wasmReady && accessorRaw?.[0].byteLength > 0
            ? parseParquetBuffers(accessorRaw).getChildAt(0)
            : null
          : (accessorRaw as arrow.Vector | null),
      );
    };
    callback();
  }, [wasmReady, accessorRaw]);

  return [accessorValue];
}

export function parseAccessor(accessorRaw: AccessorRaw): arrow.Vector | null {
  return Array.isArray(accessorRaw) && accessorRaw?.[0] instanceof DataView
    ? accessorRaw?.[0].byteLength > 0
      ? parseParquetBuffers(accessorRaw).getChildAt(0)
      : null
    : (accessorRaw as arrow.Vector | null);
}

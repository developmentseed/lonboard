import * as arrow from "apache-arrow";

import { deserializeArrowTable } from "./serialization/index.js";

type AccessorRaw = DataView[] | unknown;

export function parseAccessor(accessorRaw: AccessorRaw): arrow.Vector | null {
  return accessorRaw instanceof Array && accessorRaw?.[0] instanceof DataView
    ? accessorRaw?.[0].byteLength > 0
      ? deserializeArrowTable(accessorRaw).getChildAt(0)
      : null
    : (accessorRaw as arrow.Vector | null);
}

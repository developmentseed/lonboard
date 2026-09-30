import type { ColorAccessor, FloatAccessor } from "@geoarrow/deck.gl-geoarrow";
import type * as ga from "@geoarrow/geoarrow-js";
import type {
  FixedSizeList,
  Float32,
  Int,
  List,
  Uint8,
  Utf8,
  Vector,
} from "apache-arrow";

export type PointVector = ga.vector.PointVector;
export type LineStringVector = ga.vector.LineStringVector;
export type PolygonVector = ga.vector.PolygonVector;
export type MultiPointVector = ga.vector.MultiPointVector;
export type MultiLineStringVector = ga.vector.MultiLineStringVector;
export type MultiPolygonVector = ga.vector.MultiPolygonVector;

type ColorVector = Vector<FixedSizeList<Uint8>>;
type FloatVector = Vector<Float32>;
export type NormalVector = Vector<FixedSizeList<Float32>>;
type PixelOffsetVector = Vector<FixedSizeList<Int>>;
export type StringVector = Vector<Utf8>;
export type TimestampVector = Vector<List<Float32>>;

export type ColorAccessorInput =
  | ColorVector
  | [number, number, number]
  | [number, number, number, number];
export type FloatAccessorInput = FloatVector | number;
export type PixelOffsetAccessorInput = PixelOffsetVector | [number, number];
export type StringAccessorInput = StringVector | string;

/** Convert color accessor input to a ColorAccessor
 *
 * If the input is a constant array, it is returned as-is. (This is a scalar)
 *
 * If the input is an Arrow vector, we access the data array at the given index.
 *
 * If the input is unset, returns `undefined`.
 */
export function accessColorData(
  accessor: ColorAccessorInput | null | undefined,
  index: number,
): ColorAccessor | undefined {
  return Array.isArray(accessor) ? accessor : accessor?.data[index];
}

/** Convert float accessor input to a FloatAccessor
 *
 * If the input is a constant number, it is returned as-is. (This is a scalar)
 *
 * If the input is an Arrow vector, we access the data array at the given index.
 *
 * If the input is unset, returns `undefined`.
 */
export function accessFloatData(
  accessor: FloatAccessorInput | null | undefined,
  index: number,
): FloatAccessor | undefined {
  return typeof accessor === "number" ? accessor : accessor?.data[index];
}

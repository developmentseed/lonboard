import * as ga from "@geoarrow/geoarrow-js";
import {
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

export type ColorVector = Vector<FixedSizeList<Uint8>>;
export type FloatVector = Vector<Float32>;
export type NormalVector = Vector<FixedSizeList<Float32>>;
export type PixelOffsetVector = Vector<FixedSizeList<Int>>;
export type StringVector = Vector<Utf8>;
export type TimestampVector = Vector<List<Float32>>;

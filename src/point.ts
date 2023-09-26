// NOTE! This file is vendored from
// https://github.com/kylebarron/deck.gl-geoarrow. Any changes should be made
// upstream there and copied here. Or ideally, figure out JS bundling and import
// it!

import {
  Accessor,
  Color,
  CompositeLayer,
  CompositeLayerProps,
  DefaultProps,
  Layer,
  LayerDataSource,
  LayersList,
  Position,
  Unit,
  assert,
} from "@deck.gl/core/typed";
import { ScatterplotLayer } from "@deck.gl/layers/typed";
import * as arrow from "@apache-arrow/es2015-esm";

const DEFAULT_COLOR: [number, number, number, number] = [0, 0, 0, 255];

/** All properties supported by GeoArrowPointLayer */
export type GeoArrowPointLayerProps = _GeoArrowPointLayerProps &
  CompositeLayerProps;

/** Properties added by GeoArrowPointLayer */
export type _GeoArrowPointLayerProps = {
  data: arrow.Table;

  /**
   * The name of the geometry column in the Arrow table. If not passed, expects
   * the geometry column to have the extension type `geoarrow.point`.
   */
  geometryColumnName?: string;

  /**
   * The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`.
   * @default 'meters'
   */
  radiusUnits?: Unit;
  /**
   * Radius multiplier.
   * @default 1
   */
  radiusScale?: number;
  /**
   * The minimum radius in pixels. This prop can be used to prevent the circle from getting too small when zoomed out.
   * @default 0
   */
  radiusMinPixels?: number;
  /**
   * The maximum radius in pixels. This prop can be used to prevent the circle from getting too big when zoomed in.
   * @default Number.MAX_SAFE_INTEGER
   */
  radiusMaxPixels?: number;

  /**
   * The units of the stroke width, one of `'meters'`, `'common'`, and `'pixels'`.
   * @default 'meters'
   */
  lineWidthUnits?: Unit;
  /**
   * Stroke width multiplier.
   * @default 1
   */
  lineWidthScale?: number;
  /**
   * The minimum stroke width in pixels. This prop can be used to prevent the line from getting too thin when zoomed out.
   * @default 0
   */
  lineWidthMinPixels?: number;
  /**
   * The maximum stroke width in pixels. This prop can be used to prevent the circle from getting too thick when zoomed in.
   * @default Number.MAX_SAFE_INTEGER
   */
  lineWidthMaxPixels?: number;

  /**
   * Draw the outline of points.
   * @default false
   */
  stroked?: boolean;
  /**
   * Draw the filled area of points.
   * @default true
   */
  filled?: boolean;
  /**
   * If `true`, rendered circles always face the camera. If `false` circles face up (i.e. are parallel with the ground plane).
   * @default false
   */
  billboard?: boolean;
  /**
   * If `true`, circles are rendered with smoothed edges. If `false`, circles are rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping circles.
   * @default true
   */
  antialiasing?: boolean;

  // /**
  //  * Center position accessor.
  //  */
  // getPosition?: Accessor<arrow.Table, Position>;
  /**
   * Radius accessor.
   * @default 1
   */
  getRadius?: Accessor<arrow.Table, number>;
  /**
   * Fill color accessor.
   * @default [0, 0, 0, 255]
   */
  getFillColor?: Accessor<arrow.Table, Color>;
  /**
   * Stroke color accessor.
   * @default [0, 0, 0, 255]
   */
  getLineColor?: Accessor<arrow.Table, Color>;
  /**
   * Stroke width accessor.
   * @default 1
   */
  getLineWidth?: Accessor<arrow.Table, number>;
};

const defaultProps: DefaultProps<GeoArrowPointLayerProps> = {
  radiusUnits: "meters",
  radiusScale: { type: "number", min: 0, value: 1 },
  radiusMinPixels: { type: "number", min: 0, value: 0 }, //  min point radius in pixels
  radiusMaxPixels: { type: "number", min: 0, value: Number.MAX_SAFE_INTEGER }, // max point radius in pixels

  lineWidthUnits: "meters",
  lineWidthScale: { type: "number", min: 0, value: 1 },
  lineWidthMinPixels: { type: "number", min: 0, value: 0 },
  lineWidthMaxPixels: {
    type: "number",
    min: 0,
    value: Number.MAX_SAFE_INTEGER,
  },

  stroked: false,
  filled: true,
  billboard: false,
  antialiasing: true,

  // getPosition: { type: "accessor", value: (x) => x },
  getRadius: { type: "accessor", value: 1 },
  getFillColor: { type: "accessor", value: DEFAULT_COLOR },
  getLineColor: { type: "accessor", value: DEFAULT_COLOR },
  getLineWidth: { type: "accessor", value: 1 },
};

function findGeometryColumnIndex(
  schema: arrow.Schema,
  extensionName: string
): number | null {
  const index = schema.fields.findIndex(
    (field) => field.metadata.get("ARROW:extension:name") === extensionName
  );
  return index !== -1 ? index : null;
}

// function convertCoordsToFixedSizeList(
//   coords:
//     | arrow.Data<arrow.FixedSizeList<arrow.Float64>>
//     | arrow.Data<arrow.Struct<{ x: arrow.Float64; y: arrow.Float64 }>>
// ): arrow.Data<arrow.FixedSizeList<arrow.Float64>> {
//   if (coords.type instanceof arrow.FixedSizeList) {
//     coords.
//   }
// }

export class GeoArrowPointLayer<
  ExtraProps extends {} = {}
> extends CompositeLayer<Required<GeoArrowPointLayerProps> & ExtraProps> {
  static defaultProps = defaultProps;
  static layerName = "GeoArrowPointLayer";

  renderLayers(): Layer<{}> | LayersList | null {
    // console.log("renderLayers");
    const { data } = this.props;

    const geometryColumnIndex = findGeometryColumnIndex(
      data.schema,
      "geoarrow.point"
    );
    if (geometryColumnIndex === null) {
      console.warn("No geoarrow.point column found.");
      return null;
    }

    const geometryColumn = data.getChildAt(geometryColumnIndex);
    if (!geometryColumn) {
      return null;
    }

    const layers: ScatterplotLayer[] = [];
    for (let i = 0; i < geometryColumn.data.length; i++) {
      const arrowData = geometryColumn.data[i];
      assert(arrowData.typeId === arrow.Type.FixedSizeList);

      const childArrays = arrowData.children;
      // Should always be length one because inside the loop this should be a
      // contiguous array
      assert(childArrays.length === 1);

      const flatCoordinateArray = childArrays[0].values;
      // console.log(flatCoordinateArray);

      const layer = new ScatterplotLayer({
        // ...this.props,
        id: `${this.props.id}-geoarrow-point-${i}`,
        data: {
          length: arrowData.length,
          attributes: {
            getPosition: { value: flatCoordinateArray, size: 2 },
          },
        },
        getFillColor: [255, 0, 0],
        getLineColor: [0, 0, 255],
        stroked: true,
        radiusMinPixels: 1,
        getPointRadius: 10,
        pointRadiusMinPixels: 0.8,
      });
      layers.push(layer);
    }

    return layers;
  }
}


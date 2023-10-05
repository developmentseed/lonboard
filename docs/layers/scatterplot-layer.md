# ScatterplotLayer

The `ScatterplotLayer` renders circles at given coordinates.

![](../img/scatterplot-layer-network-speeds.jpg)

> Screenshot from Ookla example.

```py
import geopandas as gpd
from lonboard import ScatterplotLayer

gdf = gpd.GeoDataFrame()
layer = ScatterplotLayer.from_geopandas(
    gdf,
    get_fill_color=[255, 0, 0],
)
```

## Properties

Inherits from all [Base Layer](https://deck.gl/docs/api-reference/core/layer) properties.

### Render Options

#### `radiusUnits` (`str`, optional)

* Default: `'meters'`

The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

#### `radiusScale` (`float`, optional)

* Default: `1`

A global radius multiplier for all points.

#### `lineWidthUnits` (`str`, optional)

* Default: `'meters'`

The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See [unit system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

#### `lineWidthScale` (`float`, optional)

* Default: `1`

A global line width multiplier for all points.

#### `stroked` (`bool`, optional)

* Default: `false`

Draw the outline of points.

#### `filled` (`bool`, optional)

* Default: `true`

Draw the filled area of points.

#### `radiusMinPixels` (`float`, optional)

* Default: `0`

The minimum radius in pixels. This prop can be used to prevent the circle from getting too small when zoomed out.

#### `radiusMaxPixels` (`float`, optional)

* Default: `Number.MAX_SAFE_INTEGER`

The maximum radius in pixels. This prop can be used to prevent the circle from getting too big when zoomed in.

#### `lineWidthMinPixels` (`float`, optional)

* Default: `0`

The minimum line width in pixels. This prop can be used to prevent the stroke from getting too thin when zoomed out.

#### `lineWidthMaxPixels` (`float`, optional)

* Default: `Number.MAX_SAFE_INTEGER`

The maximum line width in pixels. This prop can be used to prevent the path from getting too thick when zoomed in.

#### `billboard` (`bool`, optional)

- Default: `false`

If `true`, rendered circles always face the camera. If `false` circles face up (i.e. are parallel with the ground plane).

#### `antialiasing` (`bool`, optional)

- Default: `true`

If `true`, circles are rendered with smoothed edges. If `false`, circles are rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping circles. Also, antialiasing isn't supported in FirstPersonView.

### Data Accessors

#### `getRadius` ([Function](../../developer-guide/using-layers.md#accessors)|Number, optional)

* Default: `1`

The radius of each object, in units specified by `radiusUnits` (default meters).

* If a number is provided, it is used as the radius for all objects.
* If a function is provided, it is called on each object to retrieve its radius.

#### `getColor` ([Function](../../developer-guide/using-layers.md#accessors)|Array, optional)

* Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

* If an array is provided, it is used as the color for all objects.
* If a function is provided, it is called on each object to retrieve its color.

It will be overridden by `getLineColor` and `getFillColor` if these new accessors are specified.

#### `getFillColor` ([Function](../../developer-guide/using-layers.md#accessors)|Array, optional)

* Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

* If an array is provided, it is used as the filled color for all objects.
* If a function is provided, it is called on each object to retrieve its color.
* If not provided, it falls back to `getColor`.

#### `getLineColor` ([Function](../../developer-guide/using-layers.md#accessors)|Array, optional)

* Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

* If an array is provided, it is used as the outline color for all objects.
* If a function is provided, it is called on each object to retrieve its color.
* If not provided, it falls back to `getColor`.

#### `getLineWidth` ([Function](../../developer-guide/using-layers.md#accessors)|Number, optional)

* Default: `1`

The width of the outline of each object, in units specified by `lineWidthUnits` (default meters).

* If a number is provided, it is used as the outline width for all objects.
* If a function is provided, it is called on each object to retrieve its outline width.
* If not provided, it falls back to `strokeWidth`.

## Source

[modules/layers/src/scatterplot-layer](https://github.com/visgl/deck.gl/tree/master/modules/layers/src/scatterplot-layer)

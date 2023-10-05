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

<!-- Inherits from all [Base Layer](https://deck.gl/docs/api-reference/core/layer) properties. -->

### Render Options

#### `radius_units`

- Type: `str`, optional
- Default: `'meters'`

The units of the radius, one of `'meters'`, `'common'`, and `'pixels'`. See [unit system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

#### `radius_scale`

- Type: `float`, optional
- Default: `1`

A global radius multiplier for all points.

#### `line_width_units`

- Type: `str`, optional
- Default: `'meters'`

The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See [unit system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

#### `line_width_scale`

- Type: `float`, optional
- Default: `1`

A global line width multiplier for all points.

#### `stroked`

- Type: `bool`, optional
- Default: `False`

Draw the outline of points.

#### `filled`

- Type: `bool`, optional
- Default: `True`

Draw the filled area of points.

#### `radius_min_pixels`

- Type: `float`, optional
- Default: `0`

The minimum radius in pixels. This can be used to prevent the circle from getting too small when zoomed out.

#### `radius_max_pixels`

- Type: `float`, optional
- Default: `None`

The maximum radius in pixels. This can be used to prevent the circle from getting too big when zoomed in.

#### `line_width_min_pixels`

- Type: `float`, optional
- Default: `0`

The minimum line width in pixels. This can be used to prevent the stroke from getting too thin when zoomed out.

#### `line_width_max_pixels`

- Type: `float`, optional
- Default: `None`

The maximum line width in pixels. This can be used to prevent the stroke from getting too thick when zoomed in.

#### `billboard`

- Type: `bool`, optional
- Default: `False`

If `True`, rendered circles always face the camera. If `False` circles face up (i.e. are parallel with the ground plane).

#### `antialiasing`

- Type: `bool`, optional
- Default: `True`

If `True`, circles are rendered with smoothed edges. If `False`, circles are rendered with rough edges. Antialiasing can cause artifacts on edges of overlapping circles.

### Data Accessors

#### `get_radius`

- Type: (Number, optional)
- Default: `1`

The radius of each object, in units specified by `radius_units` (default `'meters'`).

- If a number is provided, it is used as the radius for all objects.
- If a function is provided, it is called on each object to retrieve its radius.

#### `get_fill_color`

- Type: (Array, optional)
- Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

- If an array is provided, it is used as the filled color for all objects.
- If a function is provided, it is called on each object to retrieve its color.

#### `get_line_color`

- Type: (Array, optional)
- Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

- If an array is provided, it is used as the outline color for all objects.
- If a function is provided, it is called on each object to retrieve its color.

#### `get_line_width`

- Type: (Number, optional)
- Default: `1`

The width of the outline of each object, in units specified by `line_width_units` (default `'meters'`).

- If a number is provided, it is used as the outline width for all objects.
- If a function is provided, it is called on each object to retrieve its outline width.
- If not provided, it falls back to `stroke_width`.

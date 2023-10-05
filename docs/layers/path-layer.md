# PathLayer

The `PathLayer` renders lists of coordinate points as extruded polylines with mitering.

## Properties

<!-- Inherits from all [Base Layer](https://deck.gl/docs/api-reference/core/layer) properties. -->

### Render Options

#### `width_units`

- Type: `str`, optional
- Default: `'meters'`

The units of the line width, one of `'meters'`, `'common'`, and `'pixels'`. See [unit system](https://deck.gl/docs/developer-guide/coordinate-systems#supported-units).

#### `width_scale`

- Type: `float`, optional
- Default: `1`

The path width multiplier that multiplied to all paths.

#### `width_min_pixels`

- Type: `float`, optional
- Default: `0`

The minimum path width in pixels. This prop can be used to prevent the path from getting too thin when zoomed out.

#### `width_max_pixels`

- Type: `float`, optional
- Default: `None`

The maximum path width in pixels. This prop can be used to prevent the path from getting too thick when zoomed in.

#### `cap_rounded`

- Type: `bool`, optional
- Default: `false`

Type of caps. If `true`, draw round caps. Otherwise draw square caps.

#### `joint_rounded`

- Type: `bool`, optional
- Default: `false`

Type of joint. If `true`, draw round joints. Otherwise draw miter joints.

#### `billboard`

- Type: `bool`, optional
- Default: `false`

If `true`, extrude the path in screen space (width always faces the camera).
If `false`, the width always faces up.

#### `miter_limit`

- Type: `float`, optional
- Default: `4`

The maximum extent of a joint in ratio to the stroke width.
Only works if `jointRounded` is `false`.

### Data Accessors

#### `get_color`

- Type: Array, optional
- Default `[0, 0, 0, 255]`

The rgba color of each object, in `r, g, b, [a]`. Each component is in the 0-255 range.

- If an array is provided, it is used as the color for all objects.
- If a function is provided, it is called on each object to retrieve its color.

#### `get_width`

- Type: Number, optional
- Default: `1`

The width of each path, in units specified by `width_units` (default `'meters'`).

- If a number is provided, it is used as the width for all paths.
- If a function is provided, it is called on each path to retrieve its width.

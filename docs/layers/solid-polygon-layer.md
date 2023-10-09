# SolidPolygonLayer

The `SolidPolygonLayer` renders filled and/or extruded polygons.

```py
import geopandas as gpd
from lonboard import SolidPolygonLayer

# A GeoDataFrame with Polygon geometries
gdf = gpd.GeoDataFrame()
layer = SolidPolygonLayer.from_geopandas(
    gdf,
    get_fill_color=[255, 0, 0],
)
```

## Properties

<!-- Inherits from all [Base Layer](../core/layer.md) properties. -->

### Render Options

#### `filled`

- Type: `bool`, optional
- Default: `True`

Whether to fill the polygons (based on the color provided by the
`get_fill_color` accessor).

#### `extruded`

- Type: `bool`, optional
- Default: `False`

Whether to extrude the polygons (based on the elevations provided by the
`get_elevation` accessor'). If set to false, all polygons will be flat, this
generates less geometry and is faster than simply returning `0` from `get_elevation`.

#### `wireframe`

- Type: `bool`, optional
- Default: `False`

Whether to generate a line wireframe of the polygon. The outline will have
"horizontal" lines closing the top and bottom polygons and a vertical line
(a "strut") for each vertex on the polygon.

#### `elevation_scale`

- (Number, optional)
- Default: `1`

Elevation multiplier. The final elevation is calculated by
  `elevation_scale * get_elevation(d)`. `elevation_scale` is a handy property to scale
all elevation without updating the data.

-*Remarks:**

- These lines are rendered with `GL.LINE` and will thus always be 1 pixel wide.
- Wireframe and solid extrusions are exclusive, you'll need to create two layers
  with the same data if you want a combined rendering effect.

### Data Accessors

#### `get_fill_color`

- Type: (Array, optional)
- Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.

- If an array is provided, it is used as the fill color for all polygons.
- If a function is provided, it is called on each polygon to retrieve its fill color.

#### `get_line_color`

- Type: (Array, optional)
- Default: `[0, 0, 0, 255]`

The rgba color is in the format of `[r, g, b, [a]]`. Each channel is a number between 0-255 and `a` is 255 if not supplied.
Only applies if `extruded: true`.

- If an array is provided, it is used as the stroke color for all polygons.
- If a function is provided, it is called on each object to retrieve its stroke color.

#### `get_elevation`

- Type: (Number, optional)
- Default: `1000`

The elevation to extrude each polygon with.
If a cartographic projection mode is used, height will be interpreted as meters,
otherwise will be in unit coordinates.
Only applies if `extruded: true`.

- If a number is provided, it is used as the elevation for all polygons.
- If a function is provided, it is called on each object to retrieve its elevation.

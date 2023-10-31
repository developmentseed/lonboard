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

::: lonboard.SolidPolygonLayer
    options:
      show_bases: false

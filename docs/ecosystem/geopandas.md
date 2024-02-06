# GeoPandas

[GeoPandas](https://geopandas.org/en/stable/) extends the Pandas data frame library to allow spatial operations on geospatial data.

All relevant Lonboard layer classes have a [`from_geopandas`](../api/layers/base-layer.md#lonboard.BaseArrowLayer.from_geopandas) method for `GeoDataFrame` input.

Some layer types, such as [`BitmapLayer`](../api/layers/bitmap-layer.md), don't have a `from_geopandas` method because the rendering isn't relevant to GeoPandas (i.e. GeoPandas doesn't store image data).

## Example

```py
import geodatasets
import geopandas as gpd
from lonboard import Map, SolidPolygonLayer

# New York City boroughs
gdf = gpd.read_file(geodatasets.get_path('nybb'))
layer = SolidPolygonLayer.from_geopandas(
    gdf,
    get_fill_color=[255, 0, 0],
)
m = Map(layer)
```

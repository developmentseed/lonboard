# SedonaDB

[SedonaDB](https://sedona.apache.org/sedonadb/latest/) is a single-node analytical database engine from the [Apache Sedona](https://sedona.apache.org/) project. It runs spatial SQL on your own machine, without a cluster, and reads formats such as [GeoParquet](https://geoparquet.org/) directly.

You can pass a SedonaDB `DataFrame` into the top-level [`viz`](../api/viz.md#viz) function to quickly inspect data.

Additionally, you can pass a SedonaDB `DataFrame` directly into the constructor of a Lonboard layer class, such as [`ScatterplotLayer`](../api/layers/scatterplot-layer.md). There is no `from_sedonadb` method because a SedonaDB `DataFrame` already provides the input that layer constructors take: it implements the [Arrow PyCapsule Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html), a standard way for Python libraries to exchange Arrow data, and it marks its geometry columns with [GeoArrow](geoarrow.md) metadata.

## Example

These examples need SedonaDB, which you can install with `pip install "apache-sedona[db]"`. They read small GeoParquet files of [Natural Earth](https://www.naturalearthdata.com/) data over HTTPS.

Quickly inspecting data with `viz`:

```py
import sedona.db
from lonboard import viz

sd = sedona.db.connect()

# Cities from Natural Earth
url = "https://raw.githubusercontent.com/geoarrow/geoarrow-data/v0.2.0/natural-earth/files/natural-earth_cities_geo.parquet"
cities = sd.read_parquet(url)
viz(cities)
```

Customizing display with a Layer constructor:

```py
import sedona.db
from lonboard import Map, ScatterplotLayer

sd = sedona.db.connect()

base_url = "https://raw.githubusercontent.com/geoarrow/geoarrow-data/v0.2.0/natural-earth/files/"
cities = sd.read_parquet(base_url + "natural-earth_cities_geo.parquet")
countries = sd.read_parquet(base_url + "natural-earth_countries_geo.parquet")

# Register the DataFrames as views so that SQL can refer to them by name
cities.to_view("cities")
countries.to_view("countries")

# Cities that fall inside a country in Africa
df = sd.sql("""
    SELECT cities.name, cities.geometry
    FROM cities
    JOIN countries ON ST_Intersects(cities.geometry, countries.geometry)
    WHERE countries.continent = 'Africa'
""")
# See ScatterplotLayer documentation for all rendering parameters
layer = ScatterplotLayer(
    df,
    get_fill_color=[255, 0, 0],
    # Keep the points visible when zoomed out
    radius_min_pixels=3,
)
m = Map(layer)
m
```

Each layer class accepts only some geometry types: `ScatterplotLayer` is for points, [`PathLayer`](../api/layers/path-layer.md) is for lines and [`PolygonLayer`](../api/layers/polygon-layer.md) is for polygons. `viz` chooses the layer class for you, and creates one layer per geometry type if a query returns a mix of points, lines and polygons.

## Coordinate Reference Systems

SedonaDB passes the coordinate reference system (CRS) of a geometry column on to Lonboard. Lonboard renders longitude and latitude coordinates (EPSG:4326), and reprojects data that arrives in another CRS.

Geometries created in SQL, such as `ST_Point(-74.0, 40.7)`, have no CRS. Lonboard will warn that no CRS exists and draw the coordinates as longitude and latitude. To set the CRS, wrap the geometry in `ST_SetSRID`, as in `ST_SetSRID(ST_Point(-74.0, 40.7), 4326)`.

## Implementation Notes

SedonaDB exports geometry columns as [Well-Known Binary](https://libgeos.org/specifications/wkb/) (WKB), a standard binary encoding of geometries, in an Arrow column tagged with the `geoarrow.wkb` extension type. When you create a layer, Lonboard parses the WKB into GeoArrow's native encoding, which stores coordinates in plain numeric arrays.

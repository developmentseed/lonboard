# GeoArrow

[GeoArrow](https://geoarrow.org/) is an in-memory data structure for storing vector geospatial data and associated attributes. Lonboard uses GeoArrow internally and is the [primary reason why Lonboard is fast](../../how-it-works#how-is-it-so-fast).

There's a burgeoning ecosystem of Python libraries that use GeoArrow directly. Creating Lonboard `Layer` objects from GeoArrow tables is the fastest way to visualize data, as no conversions are needed on the Python side.

## geoarrow-rust

[geoarrow-rust](https://geoarrow.org/geoarrow-rs/python/latest/) is a Python library implementing the GeoArrow specification with efficient spatial operations. This library has "rust" in the name because it is implemented based on the [GeoArrow Rust implementation](https://geoarrow.org/geoarrow-rs/).

```py
from geoarrow.rust.io import read_geojson
from lonboard import Map, PathLayer

path = "/path/to/file.geojson"
geo_table = read_geojson(path)

# Assuming the GeoJSON contains LineString or MultiLineString data
layer = PathLayer(table=geo_table)
m = Map(layer)
m
```

Refer to the [geoarrow-rust](https://geoarrow.org/geoarrow-rs/python/latest/) documentation for more information.

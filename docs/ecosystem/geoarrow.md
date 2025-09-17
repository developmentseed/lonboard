# GeoArrow

[GeoArrow](https://geoarrow.org/) is an in-memory data structure for storing vector geospatial data and associated attributes. Lonboard uses GeoArrow internally and is the [primary reason why Lonboard is fast](../../how-it-works#how-is-it-so-fast).

There's a burgeoning ecosystem of Python libraries that use GeoArrow directly. Creating Lonboard `Layer` objects from GeoArrow tables is the fastest way to visualize data, as no conversions are needed on the Python side.

## geoarrow-rust

[geoarrow-rust](https://geoarrow.org/geoarrow-rs/python/latest/) is a Python library implementing the GeoArrow specification. This library has "rust" in the name because it is implemented based on the [GeoArrow Rust implementation](https://geoarrow.org/geoarrow-rs/).

```py
from geoarrow.rust.io import read_flatgeobuf
from lonboard import viz, Map, PathLayer

arrow_table = read_flatgeobuf("/path/to/file.fgb")

# Dead-simple visualization
viz(arrow_table)

# Or, customize the visualization by constructing the layer directly
# This assumes the FlatGeobuf contains LineString or MultiLineString data
layer = PathLayer(
    geo_table,
    get_width=20,
    get_color=[0, 0, 255],
    width_units="meters",
    width_min_pixels=1,
)
m = Map(layer)
m
```

Refer to the [geoarrow-rust](https://geoarrow.org/geoarrow-rs/python/latest/) documentation for more information.

"""Available layer types that can be rendered on a Lonboard Map."""

# Notes:
# - When we pass a value of `None` as a default value to a trait, that value will be
#   serialized to JS as `null` and will not be passed into the GeoArrow model (see the
#   lengthy assignments of type `..(isDefined(this.param) && { param: this.param })`).
#   Then the default value in the JS GeoArrow layer (defined in
#   `@geoarrow/deck.gl-layers`) will be used.

from ._arc import ArcLayer
from ._base import BaseArrowLayer, BaseLayer
from ._bitmap import BitmapLayer, BitmapTileLayer
from ._column import ColumnLayer
from ._heatmap import HeatmapLayer
from ._path import PathLayer
from ._point_cloud import PointCloudLayer
from ._polygon import PolygonLayer, SolidPolygonLayer
from ._scatterplot import ScatterplotLayer
from ._trips import TripsLayer

__all__ = [
    "ArcLayer",
    "BaseArrowLayer",
    "BaseLayer",
    "BitmapLayer",
    "BitmapTileLayer",
    "ColumnLayer",
    "HeatmapLayer",
    "PathLayer",
    "PointCloudLayer",
    "PolygonLayer",
    "ScatterplotLayer",
    "SolidPolygonLayer",
    "TripsLayer",
]

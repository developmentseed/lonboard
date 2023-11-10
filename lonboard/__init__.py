"""Python library for fast, interactive geospatial vector data visualization in Jupyter.
"""

from . import colormap, traits
from ._layer import HeatmapLayer, PathLayer, ScatterplotLayer, SolidPolygonLayer
from ._map import Map
from ._version import __version__
from ._viz import viz

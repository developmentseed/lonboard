"""New traits for our custom serialization.

Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html for
documentation on how to define new traitlet types.
"""

from ._a5 import A5Accessor
from ._base import FixedErrorTraitType, VariableLengthTuple
from ._color import ColorAccessor
from ._extensions import DashArrayAccessor, FilterCategoryAccessor, FilterValueAccessor
from ._float import FloatAccessor
from ._h3 import H3Accessor
from ._map import BasemapUrl, MapHeightTrait, ViewStateTrait
from ._normal import NormalAccessor
from ._point import PointAccessor
from ._raster import ProjectionTrait, TileMatrixSetTrait
from ._table import ArrowTableTrait
from ._text import TextAccessor
from ._timestamp import TimestampAccessor
from ._upstream_wrappers import Any, Bool, Enum, Float, Int, List, Tuple, Unicode, Union

__all__ = [
    "A5Accessor",
    "Any",
    "ArrowTableTrait",
    "BasemapUrl",
    "Bool",
    "ColorAccessor",
    "DashArrayAccessor",
    "Enum",
    "FilterCategoryAccessor",
    "FilterValueAccessor",
    "FixedErrorTraitType",
    "Float",
    "FloatAccessor",
    "H3Accessor",
    "Int",
    "List",
    "MapHeightTrait",
    "NormalAccessor",
    "PointAccessor",
    "ProjectionTrait",
    "TextAccessor",
    "TileMatrixSetTrait",
    "TimestampAccessor",
    "Tuple",
    "Unicode",
    "Union",
    "VariableLengthTuple",
    "ViewStateTrait",
]

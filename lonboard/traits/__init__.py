"""New traits for our custom serialization.

Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html for
documentation on how to define new traitlet types.
"""

from ._a5 import A5Accessor
from ._base import FixedErrorTraitType, VariableLengthTuple
from ._color import ColorAccessor
from ._extensions import DashArrayAccessor, FilterValueAccessor
from ._float import FloatAccessor
from ._h3 import H3Accessor
from ._map import BasemapUrl, MapHeightTrait, ViewStateTrait
from ._normal import NormalAccessor
from ._point import PointAccessor
from ._table import ArrowTableTrait
from ._text import TextAccessor
from ._timestamp import TimestampAccessor

__all__ = [
    "A5Accessor",
    "ArrowTableTrait",
    "BasemapUrl",
    "ColorAccessor",
    "DashArrayAccessor",
    "FilterValueAccessor",
    "FixedErrorTraitType",
    "FloatAccessor",
    "H3Accessor",
    "MapHeightTrait",
    "NormalAccessor",
    "PointAccessor",
    "TextAccessor",
    "TimestampAccessor",
    "VariableLengthTuple",
    "ViewStateTrait",
]

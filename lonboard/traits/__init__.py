"""New traits for our custom serialization.

Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html for
documentation on how to define new traitlet types.
"""

from ._base import FixedErrorTraitType, VariableLengthTuple
from ._color import ColorAccessor
from ._extensions import DashArrayAccessor, FilterValueAccessor
from ._float import FloatAccessor
from ._map import BasemapUrl, HeightTrait, ViewStateTrait
from ._normal import NormalAccessor
from ._point import PointAccessor
from ._table import ArrowTableTrait
from ._text import TextAccessor
from ._timestamp import TimestampAccessor

__all__ = [
    "ArrowTableTrait",
    "BasemapUrl",
    "ColorAccessor",
    "DashArrayAccessor",
    "FilterValueAccessor",
    "FixedErrorTraitType",
    "FloatAccessor",
    "HeightTrait",
    "NormalAccessor",
    "PointAccessor",
    "TextAccessor",
    "TimestampAccessor",
    "VariableLengthTuple",
    "ViewStateTrait",
]

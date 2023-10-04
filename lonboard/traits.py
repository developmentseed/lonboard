from __future__ import annotations

import typing as t
from typing import Any, List, Literal, Set, Tuple, Union

import ipywidgets
import numpy as np
import pyarrow as pa
import traitlets
from numpy.typing import NDArray
from traitlets.traitlets import TraitType, Undefined
from typing_extensions import Self

from lonboard.serialization import (
    COLOR_SERIALIZATION,
    FLOAT_SERIALIZATION,
    TABLE_SERIALIZATION,
)


class PyarrowTableTrait(traitlets.TraitType[pa.Table, pa.Table]):
    """A traitlets trait for a geospatial pyarrow table"""

    default_value = None
    info_text = "a pyarrow Table"

    def __init__(
        self: TraitType,
        default_value: Any = ...,
        allow_none: bool = False,
        read_only: bool | None = None,
        help: str | None = None,
        config: Any = None,
        *,
        allowed_geometry_types: Set[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(default_value, allow_none, read_only, help, config, **kwargs)
        self.tag(
            sync=True,
            allowed_geometry_types=allowed_geometry_types,
            **TABLE_SERIALIZATION,
        )

    def validate(self, obj: Self, value: Any):
        if not isinstance(value, pa.Table):
            self.error(obj, value)

        allowed_geometry_types = self.metadata.get("allowed_geometry_types")
        geometry_extension_type = value.schema.field("geometry").metadata.get(
            b"ARROW:extension:name"
        )
        if (
            allowed_geometry_types
            and geometry_extension_type not in allowed_geometry_types
        ):
            allowed_types_str = "\n".join(allowed_geometry_types)
            msg = f"Expected one of {allowed_types_str} geometry types, got {geometry_extension_type}."
            self.error(obj, value, info=msg)

        self.error(obj, value)


class ColorAccessor(traitlets.TraitType):
    """A representation of a deck.gl color accessor

    Represents either a single, scalar color with three or four values or an array

    Args:
        traitlets: _description_

    Returns:
        _description_
    """

    default_value = (255, 255, 255)
    info_text = "a tuple or list representing an RGB(A) color or numpy ndarray or pyarrow FixedSizeList representing an array of RGB(A) colors"

    def __init__(
        self: TraitType,
        default_value: Any = ...,
        allow_none: bool = False,
        read_only: bool | None = None,
        help: str | None = None,
        config: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(default_value, allow_none, read_only, help, config, **kwargs)
        self.tag(sync=True, **COLOR_SERIALIZATION)

    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], NDArray[np.uint8]]:
        if isinstance(value, (tuple, list)):
            if len(value) < 3 or len(value) > 4:
                self.error(
                    obj, value, info="expected 3 or 4 values if passed a tuple or list"
                )

            if any(not isinstance(v, int) for v in value):
                self.error(
                    obj,
                    value,
                    info="expected all values to be integers if passed a tuple or list",
                )

            return value

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.uint8):
                self.error(obj, value, info="Color array must be uint8 type.")

            if value.ndim != 2:
                self.error(obj, value, info="Color array must have 2 dimensions.")

            list_size = value.shape[1]
            if list_size not in (3, 4):
                self.error(
                    obj,
                    value,
                    info="Color array must have 3 or 4 as its second dimension.",
                )

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), list_size)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(
                    obj, value, info="Color pyarrow array must be a FixedSizeList."
                )

            if value.type.list_size not in (3, 4):
                self.error(
                    obj,
                    value,
                    info="Color pyarrow array must have a FixedSizeList inner size of 3 or 4.",
                )

            if not pa.types.is_uint8(value.type.value_type):
                self.error(
                    obj, value, info="Color pyarrow array must have a uint8 child."
                )

            return value

        self.error(obj, value)
        assert False


# class MyWidget1(ipywidgets.Widget):
#     c = ColorAccessor()


# w = MyWidget1(c=("127.0.0.1", 0))
# MyWidget1.__mro__


# def float_accessor():
#     return traitlets.Any().tag(sync=True, **FLOAT_SERIALIZATION)


# G = t.TypeVar("G")
# S = t.TypeVar("S")


# # Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html
# class TCPAddress(TraitType[G, S]):
#     """A trait for an (ip, port) tuple.

#     This allows for both IPv4 IP addresses as well as hostnames.
#     """

#     default_value = ("127.0.0.1", 0)
#     info_text = "an (ip, port) tuple"

#     if t.TYPE_CHECKING:

#         @t.overload
#         def __init__(
#             self: TCPAddress[tuple[str, int], tuple[str, int]],
#             default_value: bool | traitlets.Sentinel = ...,
#             allow_none: Literal[False] = ...,
#             read_only: bool | None = ...,
#             help: str | None = ...,
#             config: t.Any = ...,
#             **kwargs: t.Any,
#         ) -> None:
#             ...

#         @t.overload
#         def __init__(
#             self: TCPAddress[tuple[str, int] | None, tuple[str, int] | None],
#             default_value: bool | None | traitlets.Sentinel = ...,
#             allow_none: Literal[True] = ...,
#             read_only: bool | None = ...,
#             help: str | None = ...,
#             config: t.Any = ...,
#             **kwargs: t.Any,
#         ) -> None:
#             ...

#         def __init__(
#             self: TCPAddress[tuple[str, int] | None, tuple[str, int] | None]
#             | TCPAddress[tuple[str, int], tuple[str, int]],
#             default_value: bool | None | traitlets.Sentinel = Undefined,
#             allow_none: Literal[True, False] = False,
#             read_only: bool | None = None,
#             help: str | None = None,
#             config: t.Any = None,
#             **kwargs: t.Any,
#         ) -> None:
#             ...

#     def validate(self, obj, value):
#         if isinstance(value, tuple):
#             if len(value) == 2:
#                 if isinstance(value[0], str) and isinstance(value[1], int):
#                     port = value[1]
#                     if port >= 0 and port <= 65535:
#                         return value
#         self.error(obj, value)

#     def from_string(self, s):
#         if self.allow_none and s == "None":
#             return None
#         if ":" not in s:
#             raise ValueError("Require `ip:port`, got %r" % s)
#         ip, port = s.split(":", 1)
#         port = int(port)
#         return (ip, port)


# class MyWidget(ipywidgets.Widget):
#     c = TCPAddress()


# w = MyWidget()

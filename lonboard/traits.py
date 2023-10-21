"""New traits for our custom serialization.

Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html for
documentation on how to define new traitlet types.
"""

from __future__ import annotations

from typing import Any, List, Set, Tuple, Union

import numpy as np
import pyarrow as pa
import traitlets
from traitlets.traitlets import TraitType
from typing_extensions import Self

from lonboard.serialization import (
    COLOR_SERIALIZATION,
    FLOAT_SERIALIZATION,
    TABLE_SERIALIZATION,
)


class PyarrowTableTrait(traitlets.TraitType):
    """A traitlets trait for a geospatial pyarrow table"""

    default_value = None
    info_text = "a pyarrow Table"

    def __init__(
        self: TraitType,
        *args,
        allowed_geometry_types: Set[bytes] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
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
            msg = (
                f"Expected one of {allowed_types_str} geometry types, "
                "got {geometry_extension_type}."
            )
            self.error(obj, value, info=msg)

        return value


class ColorAccessor(traitlets.TraitType):
    """A representation of a deck.gl color accessor.

    Various input is allowed:

    - A `list` or `tuple` with three or four integers, ranging between 0 and 255
      (inclusive). This will be used as the color for all objects.
    - A numpy `ndarray` with two dimensions and data type [`np.uint8`][numpy.uint8]. The
      size of the second dimension must be `3` or `4`, and will correspond to either RGB
      or RGBA colors.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The inner
      size of the fixed size list must be `3` or `4` and its child must have type
      `uint8`.

    You can use helpers in the `lonboard.colormap` module (i.e.
    [`apply_continuous_cmap`][lonboard.colormap.apply_continuous_cmap]) to simplify
    constructing numpy arrays for color values.
    """

    default_value = (0, 0, 0)
    info_text = (
        "a tuple or list representing an RGB(A) color or numpy ndarray or "
        "pyarrow FixedSizeList representing an array of RGB(A) colors"
    )

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **COLOR_SERIALIZATION)

    # TODO: subclass self.error so that `info` is actually printed?
    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], pa.ChunkedArray, pa.FixedSizeListArray]:
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

            if any(v < 0 or v > 255 for v in value):
                self.error(
                    obj,
                    value,
                    info="expected values between 0 and 255",
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
                    info=(
                        "Color pyarrow array must have a FixedSizeList inner size of "
                        "3 or 4."
                    ),
                )

            if not pa.types.is_uint8(value.type.value_type):
                self.error(
                    obj, value, info="Color pyarrow array must have a uint8 child."
                )

            return value

        self.error(obj, value)
        assert False


class FloatAccessor(traitlets.TraitType):
    """A representation of a deck.gl float accessor.

    Various input is allowed:

    - An `int` or `float`. This will be used as the value for all objects.
    - A numpy `ndarray` with a numeric data type. This will be casted to an array of
      data type [`np.float32`][numpy.float32]. Each value in the array will be used as
      the value for the object at the same row index.
    - A pyarrow [`FloatArray`][pyarrow.FloatArray], [`DoubleArray`][pyarrow.DoubleArray]
      or [`ChunkedArray`][pyarrow.ChunkedArray] containing either a `FloatArray` or
      `DoubleArray`. Each value in the array will be used as the value for the object at
      the same row index.
    """

    default_value = float(0)
    info_text = (
        "a float value or numpy ndarray or pyarrow array representing an array"
        " of floats"
    )

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **FLOAT_SERIALIZATION)

    # TODO: subclass self.error so that `info` is actually printed?
    def validate(self, obj, value) -> Union[float, pa.ChunkedArray, pa.DoubleArray]:
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.number):
                self.error(obj, value, info="Expected numeric dtype")

            # TODO: should we always be casting to float32? Should it be
            # possible/allowed to pass in ~int8 or a data type smaller than float32?
            return pa.array(value.astype(np.float32))

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_floating(value.type):
                self.error(
                    obj,
                    value,
                    info="Float pyarrow array must be a floating point type.",
                )

            return value.cast(pa.float32())

        self.error(obj, value)
        assert False

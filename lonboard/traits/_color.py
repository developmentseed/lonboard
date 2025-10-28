# ruff: noqa: C901, PLR0912, SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, fixed_size_list_array

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard._vendor.matplotlib.colors import _to_rgba_no_colorcycle
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class ColorAccessor(FixedErrorTraitType):
    """A trait to validate input for a deck.gl color accessor.

    Various input is allowed:

    - A `list` or `tuple` with three or four integers, ranging between 0 and 255
      (inclusive). This will be used as the color for all objects.
    - A `str` representing a hex color or "well known" color interpretable by
      [matplotlib.colors.to_rgba][matplotlib.colors.to_rgba]. See also matplotlib's
      [list of named
      colors](https://matplotlib.org/stable/gallery/color/named_colors.html#base-colors).
    - A numpy `ndarray` with two dimensions and data type [`np.uint8`][numpy.uint8]. The
      size of the second dimension must be `3` or `4`, and will correspond to either RGB
      or RGBA colors.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The inner
      size of the fixed size list must be `3` or `4` and its child must have type
      `uint8`.
    - Any Arrow fixed size list array from a library that implements the [Arrow
      PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).

    You can use helpers in the [`lonboard.colormap`][lonboard.colormap] module (i.e.
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
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
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

        return ChunkedArray([fixed_size_list_array(value.ravel("C"), list_size)])

    def validate(self, obj: BaseArrowLayer, value: Any) -> tuple | list | ChunkedArray:
        if isinstance(value, (tuple, list)):
            if len(value) < 3 or len(value) > 4:
                self.error(obj, value, info="3 or 4 values if passed a tuple or list")

            if any(not isinstance(v, int) for v in value):
                self.error(
                    obj,
                    value,
                    info="all values to be integers if passed a tuple or list",
                )

            if any(v < 0 or v > 255 for v in value):
                self.error(
                    obj,
                    value,
                    info="values between 0 and 255",
                )

            return value

        if isinstance(value, str):
            try:
                c = _to_rgba_no_colorcycle(value)  # type: ignore
            except ValueError:
                return self.error(
                    obj,
                    value,
                    info=(
                        "Color string must be a named color or hex string interpretable"
                        " by matplotlib.colors.to_rgba."
                    ),
                )

            return tuple(map(int, (np.array(c) * 255).astype(np.uint8)))

        if isinstance(value, np.ndarray):
            value = self._numpy_to_arrow(obj, value)
        elif hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        if not DataType.is_fixed_size_list(value.type):
            self.error(obj, value, info="Color Arrow array must be a FixedSizeList.")

        if value.type.list_size not in (3, 4):
            self.error(
                obj,
                value,
                info=(
                    "Color Arrow array must have a FixedSizeList inner size of 3 or 4."
                ),
            )

        value_type = value.type.value_type
        assert value_type is not None
        if not DataType.is_uint8(value_type):
            self.error(obj, value, info="Color Arrow array must have a uint8 child.")

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

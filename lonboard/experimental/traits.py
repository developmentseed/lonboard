from __future__ import annotations

import warnings
from typing import Any, List, Tuple, Union

import matplotlib as mpl
import numpy as np
import pyarrow as pa
from traitlets.traitlets import TraitType

from lonboard._serialization import COLOR_SERIALIZATION, NORMAL_SERIALIZATION
from lonboard.traits import FixedErrorTraitType


class PointAccessor(FixedErrorTraitType):
    """A representation of a deck.gl point accessor.

    Various input is allowed:

    - A numpy `ndarray` with two dimensions and data type [`np.uint8`][numpy.uint8]. The
      size of the second dimension must be `2` or `3`, and will correspond to either XY
      or XYZ positions.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The inner
      size of the fixed size list must be `2` or `3` and its child must be of floating
      point type.
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

    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], pa.ChunkedArray, pa.FixedSizeListArray]:
        if isinstance(value, np.ndarray):
            if value.ndim != 2:
                self.error(obj, value, info="Point array must have 2 dimensions.")

            list_size = value.shape[1]
            if list_size not in (2, 3):
                self.error(
                    obj,
                    value,
                    info="Point array must have 2 or 3 as its second dimension.",
                )

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), list_size)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(
                    obj, value, info="Point pyarrow array must be a FixedSizeList."
                )

            if value.type.list_size not in (2, 3):
                self.error(
                    obj,
                    value,
                    info=(
                        "Color pyarrow array must have a FixedSizeList inner size of "
                        "2 or 3."
                    ),
                )

            if not pa.types.is_floating(value.type.value_type):
                self.error(
                    obj,
                    value,
                    info="Point pyarrow array must have a floating point child.",
                )

            return value

        if isinstance(value, str):
            try:
                c = mpl.colors.to_rgba(value)  # type: ignore
            except ValueError:
                self.error(
                    obj,
                    value,
                    info=(
                        "Color string must be a hex string interpretable by "
                        "matplotlib.colors.to_rgba."
                    ),
                )
                return

            return tuple(map(int, (np.array(c) * 255).astype(np.uint8)))

        self.error(obj, value)
        assert False


class NormalAccessor(Union[TraitType, FixedErrorTraitType]):
    """
    A representation of a deck.gl normal accessor

    Acceptable inputs:
    - A numpy ndarray with two dimensions: The size of the second dimension must be 3 i.e. `(N,3)`
    - a pyarrow `FixedSizeListArray` or `ChunkedArray` containing `FixedSizeListArray`s
    where the size of the inner fixed size list 3.
    """

    default_value = [0, 0, 1]
    info_text = (
        "List representing normal of each object, in [nx, ny, nz]. or numpy ndarray or "
        "pyarrow FixedSizeList representing the normal of each object, in [nx, ny, nz]"
    )

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **NORMAL_SERIALIZATION)

    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], pa.ChunkedArray, pa.FixedSizeListArray]:
        """
        Values in acceptable types must be contiguous (the same length for all values) and of floating point type
        """

        fixed_list_size = 3

        if isinstance(value, List):
            if len(value) != 3:
                self.error("Normal array must have length 3, (x,y,z)")

            if not all(isinstance(item, float) for item in value):
                self.error("All elements of Normal array must be floating point type")

            return pa.FixedSizeListArray.from_arrays(value, fixed_list_size)

        if isinstance(value, np.ndarray):
            if value.ndim != 2 or value.shape[1] != 3:
                self.error(obj, value, info="Normal array must be 2D with shape (N,3)")

            if not np.any(value == 1):
                self.error(
                    obj, value, info="One of the normal vector elements must be 1."
                )

            if not np.issubdtype(value.dtype, np.float32):
                warnings.warn(
                    "Warning: Numpy array should be floating point type. Converting to float32 point pyarrow array"
                )
                value = value.cast(pa.list_(pa.float32()))

            return pa.FixedSizeListArray.from_arrays(value, fixed_list_size)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(
                    obj, value, info="Point pyarrow array must be a FixedSizeList."
                )

            if value.type.list_size != 3:
                self.error(
                    obj,
                    value,
                    info=(
                        "Normal pyarrow array must have a FixedSizeList inner size of 3."
                    ),
                )

            if not pa.types.is_floating(value.type.value_type):
                try:
                    value = value.cast(pa.list_(pa.float32()))
                except:
                    self.error(
                        obj,
                        value,
                        info="Failed to convert array values to floating point type",
                    )

                return pa.FixedSizeListArray.from_arrays(value, fixed_list_size)

        self.error(obj, value)
        assert False

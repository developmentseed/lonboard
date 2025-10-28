# ruff: noqa: SLF001

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, Field, fixed_size_list_array

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class NormalAccessor(FixedErrorTraitType):
    """A representation of a deck.gl "normal" accessor.

    This is primarily used in the [lonboard.PointCloudLayer].

    Acceptable inputs:
    - A `list` or `tuple` with three `int` or `float` values. This will be used as the
      normal for all objects.
    - A numpy ndarray with two dimensions and floating point type. The size of the
      second dimension must be 3, i.e. its shape must be `(N, 3)`.
    - a pyarrow `FixedSizeListArray` or `ChunkedArray` containing `FixedSizeListArray`s
      where the size of the inner fixed size list 3. The child array must have type
      float32.
    - Any Arrow array that matches the above restrictions from a library that implements
      the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = (0, 0, 1)
    info_text = (
        "List representing normal of all objects in [nx, ny, nz] or numpy ndarray or "
        "pyarrow FixedSizeList representing the normal of each object, in [nx, ny, nz]"
    )

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
        if not np.issubdtype(value.dtype, np.number):
            self.error(obj, value, info="normal array to have numeric type")

        if value.ndim != 2 or value.shape[1] != 3:
            self.error(obj, value, info="normal array to be 2D with shape (N, 3)")

        if not np.issubdtype(value.dtype, np.float32):
            warnings.warn(
                """Warning: Numpy array should be float32 type.
                Converting to float32 point Arrow array""",
            )
            value = value.astype(np.float32)

        array = fixed_size_list_array(value.ravel("C"), 3)
        return ChunkedArray([array])

    def validate(
        self,
        obj: BaseArrowLayer,
        value: Any,
    ) -> tuple[int, ...] | list[int] | ChunkedArray:
        if isinstance(value, (tuple, list)):
            if len(value) != 3:
                self.error(
                    obj,
                    value,
                    info="normal scalar to have length 3, (nx, ny, nz)",
                )

            if not all(isinstance(item, (int, float)) for item in value):
                self.error(
                    obj,
                    value,
                    info="all elements of normal scalar to be int or float type",
                )

            return value

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
            self.error(obj, value, info="normal Arrow array to be a FixedSizeList.")

        if value.type.list_size != 3:
            self.error(
                obj,
                value,
                info=("normal Arrow array to have an inner size of 3."),
            )

        value_type = value.type.value_type
        assert value_type is not None
        if not DataType.is_floating(value_type):
            self.error(
                obj,
                value,
                info="Arrow array to be floating point type",
            )

        value = value.cast(DataType.list(Field("", DataType.float32()), 3))
        return value.rechunk(max_chunksize=obj._rows_per_chunk)

# ruff: noqa: SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType

from lonboard._h3._str_to_h3 import str_to_h3
from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    import pandas as pd
    from numpy.typing import NDArray
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class A5Accessor(FixedErrorTraitType):
    """A trait to validate A5 cell input.

    Various input is allowed:

    - A numpy `ndarray` with an object, S16, or uint64 data type.
    - A pandas `Series` with an object or uint64 data type.
    - A pyarrow string, large string, string view array, or uint64 array, or a chunked array of those types.
    - Any Arrow string, large string, string view array, or uint64 array, or a chunked array of those types from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = None
    info_text = (
        "a float value or numpy ndarray or Arrow array representing an array of floats"
    )

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def _pandas_to_numpy(
        self,
        obj: BaseArrowLayer,
        value: pd.Series,
    ) -> NDArray[np.str_] | NDArray[np.uint64]:
        """Cast pandas Series to numpy ndarray."""
        if isinstance(value.dtype, np.dtype) and np.issubdtype(value.dtype, np.integer):
            return np.asarray(value, dtype=np.uint64)

        if not isinstance(value.dtype, np.dtype) or not np.issubdtype(
            value.dtype,
            np.object_,
        ):
            self.error(
                obj,
                value,
                info="A5 Pandas series not object or uint64 dtype.",
            )

        if not (value.str.len() == 16).all():
            self.error(
                obj,
                value,
                info="A5 Pandas series not all 16 characters long.",
            )

        return np.asarray(value, dtype="S16")

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
        if np.issubdtype(value.dtype, np.uint64):
            return ChunkedArray([value])

        if np.issubdtype(value.dtype, np.object_):
            if {len(v) for v in value} != {16}:
                self.error(
                    obj,
                    value,
                    info="numpy object array not all 16 characters long",
                )

            value = np.asarray(value, dtype="S16")

        if not np.issubdtype(value.dtype, np.dtype("S16")):
            self.error(obj, value, info="numpy array not object, str, or uint64 dtype")

        a5_uint8_array = str_to_h3(value)
        return ChunkedArray([a5_uint8_array])

    def validate(self, obj: BaseArrowLayer, value: Any) -> ChunkedArray:
        # pandas Series
        if (
            value.__class__.__module__.startswith("pandas")
            and value.__class__.__name__ == "Series"
        ):
            value = self._pandas_to_numpy(obj, value)

        if isinstance(value, np.ndarray):
            value = self._numpy_to_arrow(obj, value)
        elif hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        if (
            DataType.is_string(value.type)
            or DataType.is_large_string(value.type)
            or DataType.is_string_view(value.type)
        ):
            value = self._numpy_to_arrow(obj, value.to_numpy())

        if not DataType.is_uint64(value.type):
            self.error(
                obj,
                value,
                info="A5 Arrow array must be uint64 type.",
            )

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

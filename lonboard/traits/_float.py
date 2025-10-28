# ruff: noqa: ARG002, SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    import pandas as pd
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class FloatAccessor(FixedErrorTraitType):
    """A trait to validate input for a deck.gl float accessor.

    Various input is allowed:

    - An `int` or `float`. This will be used as the value for all objects.
    - A numpy `ndarray` with a numeric data type. This will be casted to an array of
      data type [`np.float32`][numpy.float32]. Each value in the array will be used as
      the value for the object at the same row index.
    - A pandas `Series` with a numeric data type. This will be casted to an array of
      data type [`np.float32`][numpy.float32]. Each value in the array will be used as
      the value for the object at the same row index.
    - A pyarrow [`FloatArray`][pyarrow.FloatArray], [`DoubleArray`][pyarrow.DoubleArray]
      or [`ChunkedArray`][pyarrow.ChunkedArray] containing either a `FloatArray` or
      `DoubleArray`. Each value in the array will be used as the value for the object at
      the same row index.
    - Any Arrow floating point array from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
      This includes data structures from
      [`geoarrow-rust`](https://geoarrow.github.io/geoarrow-rs/python/latest/).
    """

    default_value = float(0)
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

    def _pandas_to_numpy(self, obj: BaseArrowLayer, value: pd.Series) -> np.ndarray:
        """Cast pandas Series to numpy ndarray."""
        return np.asarray(value)

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
        if not np.issubdtype(value.dtype, np.number):
            self.error(obj, value, info="numeric dtype")

        # TODO: should we always be casting to float32? Should it be
        # possible/allowed to pass in ~int8 or a data type smaller than float32?
        return ChunkedArray([value.astype(np.float32)])

    def validate(self, obj: BaseArrowLayer, value: Any) -> float | ChunkedArray:
        if isinstance(value, (int, float)):
            return float(value)

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

        if not DataType.is_numeric(value.type):
            self.error(
                obj,
                value,
                info="Float Arrow array must be a numeric type.",
            )

        value = value.cast(DataType.float32())
        return value.rechunk(max_chunksize=obj._rows_per_chunk)

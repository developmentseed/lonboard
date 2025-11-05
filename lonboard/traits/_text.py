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


class TextAccessor(FixedErrorTraitType):
    """A trait to validate input for a deck.gl text accessor.

    Various input is allowed:

    - A `str`. This will be used as the value for all objects.
    - A numpy `ndarray` with a string data type. Each value in the array will be used as
      the value for the object at the same row index.
    - A pandas `Series` with a string data type. Each value in the array will be used as
      the value for the object at the same row index.
    - A pyarrow [`StringArray`][pyarrow.StringArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing a `StringArray`. Each value in
      the array will be used as the value for the object at the same row index.
    """

    default_value = ""
    info_text = (
        "a string value or numpy ndarray or pandas Series or Arrow array representing"
        " an array of strings"
    )

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def _pandas_to_arrow(self, obj: BaseArrowLayer, value: pd.Series) -> ChunkedArray:
        """Cast pandas Series to arrow array."""
        try:
            import pyarrow as pa
        except ImportError as e:
            raise ImportError(
                "pyarrow is a required dependency when passing in a pandas series",
            ) from e

        return ChunkedArray([pa.array(value)])

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
        try:
            import pyarrow as pa
        except ImportError as e:
            raise ImportError(
                "pyarrow is a required dependency when passing in a numpy string array",
            ) from e

        return ChunkedArray([pa.StringArray.from_pandas(value)])

    def validate(self, obj: BaseArrowLayer, value: Any) -> float | str | ChunkedArray:
        if isinstance(value, str):
            return value

        if (
            value.__class__.__module__.startswith("pandas")
            and value.__class__.__name__ == "Series"
        ):
            value = self._pandas_to_arrow(obj, value)
        elif isinstance(value, np.ndarray):
            value = self._numpy_to_arrow(obj, value)
        elif hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        if DataType.is_large_string(value.type):
            value = value.cast(DataType.string())

        if not DataType.is_string(value.type):
            self.error(
                obj,
                value,
                info="String Arrow array must be a string type.",
            )

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

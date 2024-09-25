from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arro3.core import Array, ChunkedArray, DataType
from traitlets.traitlets import TraitType

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits import FixedErrorTraitType

if TYPE_CHECKING:
    from lonboard._layer import BaseArrowLayer


class TimestampAccessor(FixedErrorTraitType):
    """A representation of a deck.gl coordinate-timestamp accessor.

    - A pyarrow [`ListArray`][pyarrow.ListArray] containing either a numeric array. Each
        value in the array will be used as the value for the object at the same row
        index.
    - Any Arrow list array from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = None
    info_text = "a Arrow ListArray representing a nested array of timestamps"

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(self, obj: BaseArrowLayer, value) -> ChunkedArray:
        if hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        if not DataType.is_list(value.type):
            self.error(obj, value, info="timestamp array to be a list-type array")

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

from __future__ import annotations

from typing import Any, Union

import pyarrow as pa
from traitlets.traitlets import TraitType

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits import FixedErrorTraitType


class TimestampAccessor(FixedErrorTraitType):
    """A representation of a deck.gl coordinate-timestamp accessor.

    - A pyarrow [`ListArray`][pyarrow.ListArray] containing either a numeric array. Each
        value in the array will be used as the value for the object at the same row
        index.
    """

    default_value = None
    info_text = "a pyarrow ListArray representing a nested array of timestamps"

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(self, obj, value) -> Union[float, pa.ChunkedArray, pa.DoubleArray]:
        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_list(value.type):
                self.error(
                    obj,
                    value,
                    info="pyarrow array must be a list type.",
                )

            return value

        self.error(obj, value)
        assert False

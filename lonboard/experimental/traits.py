from __future__ import annotations

from typing import Any, List, Tuple, Union

import matplotlib as mpl
import numpy as np
import pyarrow as pa
from traitlets.traitlets import TraitType

from lonboard._serialization import (
    COLOR_SERIALIZATION,
)
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

# ruff: noqa: SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, Field, fixed_size_list_array

from lonboard._geoarrow.extension_types import CoordinateDimension, coord_storage_type
from lonboard._geoarrow.ops.coord_layout import convert_struct_column_to_interleaved
from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class PointAccessor(FixedErrorTraitType):
    """A representation of a deck.gl point accessor.

    Various input is allowed:

    - A numpy `ndarray` with two dimensions and data type [`np.float64`][numpy.float64].
      The size of the second dimension must be `2` or `3`, and will correspond to either
      XY or XYZ positions.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray],
      [`StructArray`][pyarrow.StructArray] or [`ChunkedArray`][pyarrow.ChunkedArray]
      containing `FixedSizeListArray`s or `StructArray`s. The inner size of the fixed
      size list must be `2` or `3` and its child must be of floating point type.
    - Any Arrow fixed size list or struct array from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = (0, 0, 0)
    info_text = "a numpy ndarray, arrow FixedSizeList, or arrow Struct representing a point array"

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def _numpy_to_arrow(self, obj: BaseArrowLayer, value: np.ndarray) -> ChunkedArray:
        if value.ndim != 2:
            self.error(obj, value, info="Point array to have 2 dimensions")

        list_size = value.shape[1]
        if list_size not in (2, 3):
            self.error(
                obj,
                value,
                info="Point array to have 2 or 3 as its second dimension",
            )

        if not np.issubdtype(value.dtype, np.float64):
            self.error(obj, value, info="Point array to have float64 type.")

        # Set geoarrow extension metadata
        field = Field(
            "",
            coord_storage_type(
                interleaved=True,
                dims=CoordinateDimension.XY
                if list_size == 2
                else CoordinateDimension.XYZ,
            ),
            nullable=True,
            metadata={"ARROW:extension:name": "geoarrow.point"},
        )
        array = fixed_size_list_array(
            value.ravel("C"),
            list_size,
            type=field,
        )

        return ChunkedArray([array])

    def validate(
        self,
        obj: BaseArrowLayer,
        value: Any,
    ) -> tuple[int, ...] | list[int] | ChunkedArray:
        if isinstance(value, np.ndarray):
            value = self._numpy_to_arrow(obj, value)
        elif hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)
        _, value = convert_struct_column_to_interleaved(field=value.field, column=value)

        if not DataType.is_fixed_size_list(value.type):
            self.error(obj, value, info="Point arrow array to be a FixedSizeList")

        if value.type.list_size not in (2, 3):
            self.error(
                obj,
                value,
                info=(
                    "point arrow array to be a FixedSizeList with list size of 2 or 3"
                ),
            )

        value_type = value.type.value_type
        assert value_type is not None
        if not DataType.is_float64(value_type):
            self.error(
                obj,
                value,
                info="Point arrow array to have a float64 point child",
            )

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

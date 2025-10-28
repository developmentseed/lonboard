# ruff: noqa: C901, PLR0912, SLF001

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from arro3.core import Array, ChunkedArray, DataType, Field, fixed_size_list_array

from lonboard._serialization import ACCESSOR_SERIALIZATION
from lonboard.traits._base import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard.layer import BaseArrowLayer


class FilterValueAccessor(FixedErrorTraitType):
    """Validate input for `get_filter_value`.

    A trait to validate input for the `get_filter_value` accessor added by the
    [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension], which can
    have between 1 and 4 float values per row.

    Various input is allowed:

    - An `int` or `float`. This will be used as the value for all objects. The
      `filter_size` of the
      [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must be 1.
    - A one-dimensional numpy `ndarray` with a numeric data type. This will be casted to
      an array of data type [`np.float32`][numpy.float32]. Each value in the array will
      be used as the value for the object at the same row index. The `filter_size` of
      the [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must be 1.
    - A two-dimensional numpy `ndarray` with a numeric data type. This will be casted to
      an array of data type [`np.float32`][numpy.float32]. Each value in the array will
      be used as the value for the object at the same row index. The `filter_size` of
      the [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must match the size of the second dimension of the array.
    - A pandas `Series` with a numeric data type. This will be casted to an array of
      data type [`np.float32`][numpy.float32]. Each value in the array will be used as
      the value for the object at the same row index. The `filter_size` of the
      [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must be 1.
    - A pyarrow [`FloatArray`][pyarrow.FloatArray], [`DoubleArray`][pyarrow.DoubleArray]
      or [`ChunkedArray`][pyarrow.ChunkedArray] containing either a `FloatArray` or
      `DoubleArray`. Each value in the array will be used as the value for the object at
      the same row index. The `filter_size` of the
      [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must be 1.

      Alternatively, you can pass any corresponding Arrow data structure from a library
      that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The child
      array of the fixed size list must be of floating point type. The `filter_size` of
      the [`DataFilterExtension`][lonboard.layer_extension.DataFilterExtension] instance
      must match the list size.

      Alternatively, you can pass any corresponding Arrow data structure from a library
      that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
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

    def _pandas_to_numpy(
        self,
        obj: BaseArrowLayer,
        value: Any,
        filter_size: int,
    ) -> np.ndarray:
        # Assert that filter_size == 1 for a pandas series.
        # Pandas series can technically contain Python list objects inside them, but
        # for simplicity we disallow that.
        if filter_size != 1:
            self.error(obj, value, info="filter_size==1 with pandas Series")

        # Cast pandas Series to numpy ndarray
        return np.asarray(value)

    def _numpy_to_arrow(
        self,
        obj: BaseArrowLayer,
        value: Any,
        filter_size: int,
    ) -> ChunkedArray:
        if not np.issubdtype(value.dtype, np.number):
            self.error(obj, value, info="numeric dtype")

        # Cast to float32
        value = value.astype(np.float32)

        if len(value.shape) == 1:
            if filter_size != 1:
                self.error(obj, value, info="filter_size==1 with 1-D numpy array")

            return ChunkedArray([value])

        if len(value.shape) != 2:
            self.error(obj, value, info="1-D or 2-D numpy array")

        if value.shape[1] != filter_size:
            self.error(
                obj,
                value,
                info=(
                    f"filter_size ({filter_size}) to match 2nd dimension of numpy array"
                ),
            )

        array = fixed_size_list_array(value.ravel("C"), filter_size)
        return ChunkedArray([array])

    def validate(
        self,
        obj: BaseArrowLayer,
        value: Any,
    ) -> float | tuple | list | ChunkedArray:
        # Find the data filter extension in the attributes of the parent object so we
        # can validate against the filter size.
        data_filter_extension = [
            ext
            for ext in obj.extensions
            if ext._extension_type == "data-filter"  # type: ignore
        ]
        assert len(data_filter_extension) == 1
        filter_size = data_filter_extension[0].filter_size  # type: ignore

        if isinstance(value, (int, float)):
            if filter_size != 1:
                self.error(obj, value, info="filter_size==1 with scalar value")

            return float(value)

        if isinstance(value, (tuple, list)):
            if filter_size != len(value):
                self.error(
                    obj,
                    value,
                    info=f"filter_size ({filter_size}) to match length of tuple/list",
                )

            if any(not isinstance(v, (int, float)) for v in value):
                self.error(
                    obj,
                    value,
                    info="all values in tuple or list to be numeric",
                )

            return value

        # pandas Series
        if (
            value.__class__.__module__.startswith("pandas")
            and value.__class__.__name__ == "Series"
        ):
            value = self._pandas_to_numpy(obj, value, filter_size)

        if isinstance(value, np.ndarray):
            value = self._numpy_to_arrow(obj, value, filter_size)
        elif hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        # Allowed inputs are either a FixedSizeListArray or numeric array.
        # If not a fixed size list array, check for floating and cast to float32
        if not DataType.is_fixed_size_list(value.type):
            if filter_size != 1:
                self.error(
                    obj,
                    value,
                    info="filter_size==1 with non-FixedSizeList type arrow array",
                )

            if not DataType.is_floating(value.type):
                self.error(
                    obj,
                    value,
                    info="arrow array to be a floating point type",
                )

            return value.cast(DataType.float32())

        # We have a FixedSizeListArray
        if filter_size != value.type.list_size:
            self.error(
                obj,
                value,
                info=(
                    f"filter_size ({filter_size}) to match list size of "
                    "FixedSizeList arrow array"
                ),
            )

        value_type = value.type.value_type
        assert value_type is not None
        if not DataType.is_floating(value_type):
            self.error(
                obj,
                value,
                info="arrow array to have floating point child type",
            )

        # Cast values to float32
        value = value.cast(
            DataType.list(Field("", DataType.float32()), value.type.list_size),
        )
        return value.rechunk(max_chunksize=obj._rows_per_chunk)


class DashArrayAccessor(FixedErrorTraitType):
    """A trait to validate input for a deck.gl dash accessor.

    Primarily used in
    [`PathStyleExtension`][lonboard.layer_extension.PathStyleExtension].

    Various input is allowed:

    - A `list` or `tuple` with 2 integers. This defines the dash size and gap size
      respectively.
    - A numpy `ndarray` with two dimensions and numeric data type. The size of the
      second dimension must be `2`.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The inner
      size of the fixed size list must be `2`.
    - Any Arrow fixed size list array from a library that implements the [Arrow
      PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = (0, 0)
    info_text = (
        "a tuple or list or numpy ndarray or "
        "pyarrow FixedSizeList representing dash size and gap size."
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
            self.error(obj, value, info="NumPy array must be uint8 type.")

        if value.ndim != 2:
            self.error(obj, value, info="NumPy array must have 2 dimensions.")

        list_size = value.shape[1]
        if list_size != 2:
            self.error(
                obj,
                value,
                info="NumPy array must have 2 as its second dimension.",
            )

        # Cast float64 to float32; leave other data types the same
        if np.issubdtype(value.dtype, np.float64):
            value = value.astype(np.float32)

        array = fixed_size_list_array(value.ravel("C"), list_size)
        return ChunkedArray([array])

    def validate(
        self,
        obj: BaseArrowLayer,
        value: Any,
    ) -> tuple[int, ...] | list[int] | ChunkedArray:
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                self.error(obj, value, info="2 value list only")

            if any(not isinstance(v, (int, float)) for v in value):
                self.error(
                    obj,
                    value,
                    info="all values to be int or float type if passed a tuple or list",
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
            self.error(obj, value, info="Arrow array must be a FixedSizeList.")

        if value.type.list_size != 2:
            self.error(
                obj,
                value,
                info="Arrow array must have a FixedSizeList inner size of 2.",
            )

        value_type = value.type.value_type
        assert value_type is not None
        if not (
            DataType.is_integer(value_type)
            or DataType.is_signed_integer(value_type)
            or DataType.is_floating(value_type)
        ):
            self.error(obj, value, info="Arrow array to have a numeric type child.")

        # Cast float64 to float32; leave other data types the same
        if DataType.is_float64(value_type):
            value = value.cast(DataType.list(DataType.float32(), value.type.list_size))

        return value.rechunk(max_chunksize=obj._rows_per_chunk)

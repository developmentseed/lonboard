from __future__ import annotations

from typing import Any, List, Tuple, Union

import matplotlib as mpl
import numpy as np
import pyarrow as pa
from traitlets.traitlets import TraitType

from lonboard._serialization import ACCESSOR_SERIALIZATION
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
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], pa.ChunkedArray, pa.FixedSizeListArray]:
        if isinstance(value, np.ndarray):
            if value.ndim != 2:
                self.error(obj, value, info="Point array to have 2 dimensions")

            list_size = value.shape[1]
            if list_size not in (2, 3):
                self.error(
                    obj,
                    value,
                    info="Point array to have 2 or 3 as its second dimension",
                )

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), list_size)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(obj, value, info="Point pyarrow array to be a FixedSizeList")

            if value.type.list_size not in (2, 3):
                self.error(
                    obj,
                    value,
                    info=(
                        "Color pyarrow array to be a FixedSizeList with list size of "
                        "2 or 3"
                    ),
                )

            if not pa.types.is_floating(value.type.value_type):
                self.error(
                    obj,
                    value,
                    info="Point pyarrow array to have a floating point child",
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
                        "Color string to be a hex string interpretable by "
                        "matplotlib.colors.to_rgba"
                    ),
                )
                return

            return tuple(map(int, (np.array(c) * 255).astype(np.uint8)))

        self.error(obj, value)
        assert False


class GetFilterValueAccessor(FixedErrorTraitType):
    """
    A trait to validate input for the `get_filter_value` accessor added by the
    [`DataFilterExtension`][lonboard.experimental.DataFilterExtension], which can have
    between 1 and 4 float values per row.

    Various input is allowed:

    - An `int` or `float`. This will be used as the value for all objects. The
      `filter_size` of the
      [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance must
      be 1.
    - A one-dimensional numpy `ndarray` with a numeric data type. This will be casted to
      an array of data type [`np.float32`][numpy.float32]. Each value in the array will
      be used as the value for the object at the same row index. The `filter_size` of
      the [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance
      must be 1.
    - A two-dimensional numpy `ndarray` with a numeric data type. This will be casted to
      an array of data type [`np.float32`][numpy.float32]. Each value in the array will
      be used as the value for the object at the same row index. The `filter_size` of
      the [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance
      must match the size of the second dimension of the array.
    - A pandas `Series` with a numeric data type. This will be casted to an array of
      data type [`np.float32`][numpy.float32]. Each value in the array will be used as
      the value for the object at the same row index. The `filter_size` of
      the [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance
      must be 1.
    - A pyarrow [`FloatArray`][pyarrow.FloatArray], [`DoubleArray`][pyarrow.DoubleArray]
      or [`ChunkedArray`][pyarrow.ChunkedArray] containing either a `FloatArray` or
      `DoubleArray`. Each value in the array will be used as the value for the object at
      the same row index. The `filter_size` of the
      [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance must
      be 1.

      Alternatively, you can pass any corresponding Arrow data structure from a library
      that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The child
      array of the fixed size list must be of floating point type. The `filter_size` of
      the [`DataFilterExtension`][lonboard.experimental.DataFilterExtension] instance
      must match the list size.

      Alternatively, you can pass any corresponding Arrow data structure from a library
      that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = float(0)
    info_text = (
        "a float value or numpy ndarray or pyarrow array representing an array"
        " of floats"
    )

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(self, obj, value) -> Union[float, pa.ChunkedArray, pa.DoubleArray]:
        # Find the data filter extension in the attributes of the parent object so we
        # can validate against the filter size.
        data_filter_extension = [
            ext for ext in obj.extensions if ext._extension_type == "data-filter"
        ]
        assert len(data_filter_extension) == 1
        filter_size = data_filter_extension[0].filter_size

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
            # Assert that filter_size == 1 for a pandas series.
            # Pandas series can technically contain Python list objects inside them, but
            # for simplicity we disallow that.
            if filter_size != 1:
                self.error(obj, value, info="filter_size==1 with pandas Series")

            # Cast pandas Series to numpy ndarray
            value = np.asarray(value)

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.number):
                self.error(obj, value, info="numeric dtype")

            # Cast to float32
            value = value.astype(np.float32)

            if len(value.shape) == 1:
                if filter_size != 1:
                    self.error(obj, value, info="filter_size==1 with 1-D numpy array")

                return pa.array(value)

            if len(value.shape) != 2:
                self.error(obj, value, info="1-D or 2-D numpy array")

            if value.shape[1] != filter_size:
                self.error(
                    obj,
                    value,
                    info=(
                        f"filter_size ({filter_size}) to match 2nd dimension of "
                        "numpy array"
                    ),
                )

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), filter_size)

        # Check for Arrow PyCapsule Interface
        # https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html
        # TODO: with pyarrow v16 also import chunked array from stream
        if not isinstance(value, (pa.ChunkedArray, pa.Array)):
            if hasattr(value, "__arrow_c_array__"):
                value = pa.array(value)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            # Allowed inputs are either a FixedSizeListArray or numeric array.
            # If not a fixed size list array, check for floating and cast to float32
            if not pa.types.is_fixed_size_list(value.type):
                if filter_size != 1:
                    self.error(
                        obj,
                        value,
                        info="filter_size==1 with non-FixedSizeList type arrow array",
                    )

                if not pa.types.is_floating(value.type):
                    self.error(
                        obj,
                        value,
                        info="arrow array to be a floating point type",
                    )

                return value.cast(pa.float32())

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

            if not pa.types.is_floating(value.type.value_type):
                self.error(
                    obj,
                    value,
                    info="arrow array to have floating point child type",
                )

            # Cast values to float32
            return value.cast(pa.list_(pa.float32(), value.type.list_size))

        self.error(obj, value)
        assert False

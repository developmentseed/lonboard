"""New traits for our custom serialization.

Refer to https://traitlets.readthedocs.io/en/stable/defining_traits.html for
documentation on how to define new traitlet types.
"""

from __future__ import annotations

import warnings
from typing import Any, List, Optional, Set, Tuple, Union, cast

import matplotlib as mpl
import numpy as np
import pyarrow as pa
import traitlets
from traitlets import TraitError
from traitlets.traitlets import TraitType
from traitlets.utils.descriptions import class_of, describe
from typing_extensions import Self

from lonboard._serialization import (
    ACCESSOR_SERIALIZATION,
    TABLE_SERIALIZATION,
)
from lonboard._utils import get_geometry_column_index


# This is a custom subclass of traitlets.TraitType because its `error` method ignores
# the `info` passed in. See https://github.com/developmentseed/lonboard/issues/71 and
# https://github.com/ipython/traitlets/pull/884
class FixedErrorTraitType(traitlets.TraitType):
    def error(self, obj: Self, value, error=None, info=None):
        """Raise a TraitError

        Parameters
        ----------
        obj : HasTraits or None
            The instance which owns the trait. If not
            object is given, then an object agnostic
            error will be raised.
        value : any
            The value that caused the error.
        error : Exception (default: None)
            An error that was raised by a child trait.
            The arguments of this exception should be
            of the form ``(value, info, *traits)``.
            Where the ``value`` and ``info`` are the
            problem value, and string describing the
            expected value. The ``traits`` are a series
            of :class:`TraitType` instances that are
            "children" of this one (the first being
            the deepest).
        info : str (default: None)
            A description of the expected value. By
            default this is infered from this trait's
            ``info`` method.
        """
        if error is not None:
            # handle nested error
            error.args += (self,)
            if self.name is not None:
                # this is the root trait that must format the final message
                chain = " of ".join(describe("a", t) for t in error.args[2:])
                if obj is not None:
                    error.args = (
                        "The '{}' trait of {} instance contains {} which "
                        "expected {}, not {}.".format(
                            self.name,
                            describe("an", obj),
                            chain,
                            error.args[1],
                            describe("the", error.args[0]),
                        ),
                    )
                else:
                    error.args = (
                        "The '{}' trait contains {} which "
                        "expected {}, not {}.".format(
                            self.name,
                            chain,
                            error.args[1],
                            describe("the", error.args[0]),
                        ),
                    )
            raise error
        else:
            # this trait caused an error
            if self.name is None:
                # this is not the root trait
                raise TraitError(value, info or self.info(), self)
            else:
                # this is the root trait
                if obj is not None:
                    e = "The '{}' trait of {} instance expected {}, not {}.".format(
                        self.name,
                        class_of(obj),
                        # CHANGED:
                        # Use info if provided
                        info or self.info(),
                        describe("the", value),
                    )
                else:
                    e = "The '{}' trait expected {}, not {}.".format(
                        self.name,
                        # CHANGED:
                        # Use info if provided
                        info or self.info(),
                        describe("the", value),
                    )
                raise TraitError(e)


class PyarrowTableTrait(FixedErrorTraitType):
    """A trait to validate input for a geospatial Arrow-backed table

    Allowed input includes:

    - A pyarrow [`Table`][pyarrow.Table] or containing a geometry column with [GeoArrow metadata](https://geoarrow.org/extension-types).
    - Any GeoArrow table from a library that implements the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
      This includes the
      [`GeoTable`](https://geoarrow.github.io/geoarrow-rs/python/latest/api/core/table/#geoarrow.rust.core.GeoTable)
      class from
      [`geoarrow-rust`](https://geoarrow.github.io/geoarrow-rs/python/latest/).
    """

    default_value = None
    info_text = "a pyarrow or GeoArrow Table"

    def __init__(
        self: TraitType,
        *args,
        allowed_geometry_types: Set[bytes] | None = None,
        allowed_dimensions: Optional[Set[int]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(
            sync=True,
            allowed_geometry_types=allowed_geometry_types,
            allowed_dimensions=allowed_dimensions,
            **TABLE_SERIALIZATION,
        )

    def validate(self, obj: Self, value: Any):
        if not isinstance(value, pa.Table):
            self.error(obj, value)

        allowed_geometry_types = self.metadata.get("allowed_geometry_types")
        allowed_geometry_types = cast(Optional[Set[bytes]], allowed_geometry_types)

        allowed_dimensions = self.metadata.get("allowed_dimensions")
        allowed_dimensions = cast(Optional[Set[int]], allowed_dimensions)

        geom_col_idx = get_geometry_column_index(value.schema)

        # No restriction on the allowed geometry types in this table
        if allowed_geometry_types:
            geometry_extension_type = value.schema.field(geom_col_idx).metadata.get(
                b"ARROW:extension:name"
            )

            if (
                allowed_geometry_types
                and geometry_extension_type not in allowed_geometry_types
            ):
                allowed_types_str = ", ".join(map(str, allowed_geometry_types))
                msg = (
                    f"Expected one of {allowed_types_str} geometry types, "
                    f"got {geometry_extension_type}."
                )
                self.error(obj, value, info=msg)

        if allowed_dimensions:
            typ = value.column(geom_col_idx).type
            while isinstance(typ, pa.ListType):
                typ = typ.value_type

            assert isinstance(typ, pa.FixedSizeListType)
            if typ.list_size not in allowed_dimensions:
                msg = " or ".join(map(str, list(allowed_dimensions)))
                self.error(obj, value, info=f"{msg}-dimensional points")

        return value


class ColorAccessor(FixedErrorTraitType):
    """A trait to validate input for a deck.gl color accessor.

    Various input is allowed:

    - A `list` or `tuple` with three or four integers, ranging between 0 and 255
      (inclusive). This will be used as the color for all objects.
    - A `str` representing a hex color or "well known" color interpretable by
      [matplotlib.colors.to_rgba][matplotlib.colors.to_rgba].
    - A numpy `ndarray` with two dimensions and data type [`np.uint8`][numpy.uint8]. The
      size of the second dimension must be `3` or `4`, and will correspond to either RGB
      or RGBA colors.
    - A pyarrow [`FixedSizeListArray`][pyarrow.FixedSizeListArray] or
      [`ChunkedArray`][pyarrow.ChunkedArray] containing `FixedSizeListArray`s. The inner
      size of the fixed size list must be `3` or `4` and its child must have type
      `uint8`.
    - Any Arrow fixed size list array from a library that implements the [Arrow
      PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).

    You can use helpers in the [`lonboard.colormap`][lonboard.colormap] module (i.e.
    [`apply_continuous_cmap`][lonboard.colormap.apply_continuous_cmap]) to simplify
    constructing numpy arrays for color values.
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
        if isinstance(value, (tuple, list)):
            if len(value) < 3 or len(value) > 4:
                self.error(obj, value, info="3 or 4 values if passed a tuple or list")

            if any(not isinstance(v, int) for v in value):
                self.error(
                    obj,
                    value,
                    info="all values to be integers if passed a tuple or list",
                )

            if any(v < 0 or v > 255 for v in value):
                self.error(
                    obj,
                    value,
                    info="values between 0 and 255",
                )

            return value

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.uint8):
                self.error(obj, value, info="Color array must be uint8 type.")

            if value.ndim != 2:
                self.error(obj, value, info="Color array must have 2 dimensions.")

            list_size = value.shape[1]
            if list_size not in (3, 4):
                self.error(
                    obj,
                    value,
                    info="Color array must have 3 or 4 as its second dimension.",
                )

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), list_size)

        # Check for Arrow PyCapsule Interface
        # https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html
        # TODO: with pyarrow v16 also import chunked array from stream
        if not isinstance(value, (pa.ChunkedArray, pa.Array)):
            if hasattr(value, "__arrow_c_array__"):
                value = pa.array(value)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(
                    obj, value, info="Color pyarrow array must be a FixedSizeList."
                )

            if value.type.list_size not in (3, 4):
                self.error(
                    obj,
                    value,
                    info=(
                        "Color pyarrow array must have a FixedSizeList inner size of "
                        "3 or 4."
                    ),
                )

            if not pa.types.is_uint8(value.type.value_type):
                self.error(
                    obj, value, info="Color pyarrow array must have a uint8 child."
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
        if isinstance(value, (int, float)):
            return float(value)

        # pandas Series
        if (
            value.__class__.__module__.startswith("pandas")
            and value.__class__.__name__ == "Series"
        ):
            # Cast pandas Series to numpy ndarray
            value = np.asarray(value)

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.number):
                self.error(obj, value, info="numeric dtype")

            # TODO: should we always be casting to float32? Should it be
            # possible/allowed to pass in ~int8 or a data type smaller than float32?
            return pa.array(value.astype(np.float32))

        # Check for Arrow PyCapsule Interface
        # https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html
        # TODO: with pyarrow v16 also import chunked array from stream
        if not isinstance(value, (pa.ChunkedArray, pa.Array)):
            if hasattr(value, "__arrow_c_array__"):
                value = pa.array(value)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_floating(value.type):
                self.error(
                    obj,
                    value,
                    info="Float pyarrow array must be a floating point type.",
                )

            return value.cast(pa.float32())

        self.error(obj, value)
        assert False


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
        "a string value or numpy ndarray or pandas Series or pyarrow array representing"
        " an array of strings"
    )

    def __init__(
        self: TraitType,
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(self, obj, value) -> Union[float, pa.ChunkedArray, pa.DoubleArray]:
        if isinstance(value, str):
            return value

        # pandas Series
        if (
            value.__class__.__module__.startswith("pandas")
            and value.__class__.__name__ == "Series"
        ):
            # Cast pandas Series to pyarrow array
            value = pa.array(value)

        if isinstance(value, np.ndarray):
            value = pa.StringArray.from_pandas(value)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_string(value.type):
                self.error(
                    obj,
                    value,
                    info="String pyarrow array must be a string type.",
                )

            return value

        self.error(obj, value)
        assert False


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


class NormalAccessor(FixedErrorTraitType):
    """
    A representation of a deck.gl "normal" accessor

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
        *args,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **ACCESSOR_SERIALIZATION)

    def validate(
        self, obj, value
    ) -> Union[Tuple[int, ...], List[int], pa.ChunkedArray, pa.FixedSizeListArray]:
        if isinstance(value, (tuple, list)):
            if len(value) != 3:
                self.error(
                    obj, value, info="normal scalar to have length 3, (nx, ny, nz)"
                )

            if not all(isinstance(item, (int, float)) for item in value):
                self.error(
                    obj,
                    value,
                    info="all elements of normal scalar to be int or float type",
                )

            return value

        if isinstance(value, np.ndarray):
            if not np.issubdtype(value.dtype, np.number):
                self.error(obj, value, info="normal array to have numeric type")

            if value.ndim != 2 or value.shape[1] != 3:
                self.error(obj, value, info="normal array to be 2D with shape (N, 3)")

            if not np.issubdtype(value.dtype, np.float32):
                warnings.warn(
                    """Warning: Numpy array should be float32 type.
                    Converting to float32 point pyarrow array"""
                )
                value = value.astype(np.float32)

            return pa.FixedSizeListArray.from_arrays(value.flatten("C"), 3)

        # Check for Arrow PyCapsule Interface
        # https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html
        # TODO: with pyarrow v16 also import chunked array from stream
        if not isinstance(value, (pa.ChunkedArray, pa.Array)):
            if hasattr(value, "__arrow_c_array__"):
                value = pa.array(value)

        if isinstance(value, (pa.ChunkedArray, pa.Array)):
            if not pa.types.is_fixed_size_list(value.type):
                self.error(
                    obj, value, info="normal pyarrow array to be a FixedSizeList."
                )

            if value.type.list_size != 3:
                self.error(
                    obj,
                    value,
                    info=("normal pyarrow array to have an inner size of 3."),
                )

            if not pa.types.is_floating(value.type.value_type):
                self.error(
                    obj,
                    value,
                    info="pyarrow array to be floating point type",
                )

            return value.cast(pa.list_(pa.float32(), 3))

        self.error(obj, value)
        assert False

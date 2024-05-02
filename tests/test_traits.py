import ipywidgets
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
import traitlets
from traitlets import TraitError

from lonboard._base import BaseExtension
from lonboard._layer import BaseArrowLayer, BaseLayer
from lonboard.layer_extension import DataFilterExtension
from lonboard.traits import (
    ColorAccessor,
    FloatAccessor,
    NormalAccessor,
    PyarrowTableTrait,
)


class ColorAccessorWidget(BaseLayer):
    _rows_per_chunk = 2
    # Any tests that are intended to pass validation checks must also have 3 rows, since
    # there's another length check in the serialization code.
    table = pa.table({"data": [1, 2, 3]})

    color = ColorAccessor()


def test_color_accessor_validation_list_length():
    # tuple or list must have 3 or 4 elements
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=())

    with pytest.raises(
        TraitError, match="expected 3 or 4 values if passed a tuple or list"
    ):
        ColorAccessorWidget(color=(1, 2))

    with pytest.raises(
        TraitError, match="expected 3 or 4 values if passed a tuple or list"
    ):
        ColorAccessorWidget(color=(1, 2, 3, 4, 5))

    ColorAccessorWidget(color=(1, 2, 3))
    ColorAccessorWidget(color=(1, 2, 3, 255))


def test_color_accessor_validation_list_type():
    # tuple or list must have int values
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=(1.0, 2.0, 4.0))


def test_color_accessor_validation_list_range():
    # tuple or list must have values between 0-255
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=(-1, 2, 4))

    with pytest.raises(TraitError):
        ColorAccessorWidget(color=(1, 2, 300))


def test_color_accessor_validation_dim_shape_np_arr():
    # must be two dimensions
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 3, 1))

    # Second dim must be 3 or 4
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 1))

    with pytest.raises(TraitError):
        ColorAccessorWidget(color=np.array([1, 2, 3, 4], dtype=np.uint8).reshape(-1, 2))

    with pytest.raises(TraitError):
        ColorAccessorWidget(
            color=np.array([1, 2, 3, 4, 5], dtype=np.uint8).reshape(-1, 5)
        )

    ColorAccessorWidget(
        color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 3).repeat(3, axis=0)
    )
    ColorAccessorWidget(
        color=np.array([1, 2, 3, 255], dtype=np.uint8).reshape(-1, 4).repeat(3, axis=0)
    )


def test_color_accessor_validation_np_dtype():
    # must be np.uint8
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=np.array([1, 2, 3]).reshape(-1, 3))

    ColorAccessorWidget(
        color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 3).repeat(3, axis=0)
    )


def test_color_accessor_validation_pyarrow_array_type():
    # array type must be FixedSizeList
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=pa.array(np.array([1, 2, 3], dtype=np.float64)))

    np_arr = np.array([1, 2, 3], dtype=np.uint8).repeat(3, axis=0)
    ColorAccessorWidget(color=pa.FixedSizeListArray.from_arrays(np_arr, 3))

    np_arr = np.array([1, 2, 3, 255], dtype=np.uint8).repeat(3, axis=0)
    ColorAccessorWidget(color=pa.FixedSizeListArray.from_arrays(np_arr, 4))

    # array type must have uint8 child
    np_arr = np.array([1, 2, 3, 255], dtype=np.uint64)
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=pa.FixedSizeListArray.from_arrays(np_arr, 4))


def test_color_accessor_validation_string():
    # Shortened RGB
    ColorAccessorWidget(color="#fff")

    # Shortened RGBA
    ColorAccessorWidget(color="#fff0")

    # Full RGB
    ColorAccessorWidget(color="#ffffff")

    c = ColorAccessorWidget(color="#ffffffa0")
    assert c.color[3] == 0xA0, "Expected alpha to be parsed correctly"

    # HTML Aliases
    ColorAccessorWidget(color="red")
    ColorAccessorWidget(color="blue")

    with pytest.raises(TraitError):
        ColorAccessorWidget(color="#ff")


class FloatAccessorWidget(BaseLayer):
    _rows_per_chunk = 2
    # Any tests that are intended to pass validation checks must also have 3 rows, since
    # there's another length check in the serialization code.
    table = pa.table({"data": [1, 2, 3]})

    value = FloatAccessor()


def test_float_accessor_validation_type():
    # must be int or float scalar
    with pytest.raises(TraitError):
        FloatAccessorWidget(value=())

    with pytest.raises(TraitError):
        FloatAccessorWidget(value="2")

    FloatAccessorWidget(value=2)
    FloatAccessorWidget(value=2.0)
    FloatAccessorWidget(value=np.array([2, 3, 4]))
    FloatAccessorWidget(value=np.array([2, 3, 4], dtype=np.float32))
    FloatAccessorWidget(value=np.array([2, 3, 4], dtype=np.float64))
    FloatAccessorWidget(value=pd.Series([2, 3, 4]))
    FloatAccessorWidget(value=pd.Series([2, 3, 4], dtype=np.float32))
    FloatAccessorWidget(value=pd.Series([2, 3, 4], dtype=np.float64))

    # Must be floating-point array type
    with pytest.raises(TraitError):
        FloatAccessorWidget(value=pa.array(np.array([2, 3, 4])))

    FloatAccessorWidget(value=pa.array(np.array([2, 3, 4], dtype=np.float32)))
    FloatAccessorWidget(value=pa.array(np.array([2, 3, 4], dtype=np.float64)))


class FilterValueAccessorWidget(BaseArrowLayer):
    # This needs a data filter extension in the extensions array to validate filter_size
    extensions = traitlets.List(trait=traitlets.Instance(BaseExtension)).tag(
        sync=True, **ipywidgets.widget_serialization
    )

    table = PyarrowTableTrait()

    def __init__(self, *args, **kwargs):
        # Any tests that are intended to pass validation checks must also have 3 rows,
        # since there's another length check in the serialization code.
        table = pa.table({"data": [1, 2, 3]})
        super().__init__(*args, table=table, _rows_per_chunk=3, **kwargs)


def test_filter_value_validation_filter_size_1():
    extensions = [DataFilterExtension(filter_size=1)]

    # Must pass a value
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=())

    # Strings not allowed
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value="2")

    # Lists and tuples must match filter_size
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=[1, 2])
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=(1, 2))
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=[1])
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=(1,))

    # Allow floats and ints
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=2)
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=2.0)

    # Numpy arrays
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=np.array([2, 3, 4])
    )
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=np.array([2, 3, 4], dtype=np.float32)
    )
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=np.array([2, 3, 4], dtype=np.float64)
    )
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=pd.Series([2, 3, 4])
    )
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=pd.Series([2, 3, 4], dtype=np.float32)
    )
    FilterValueAccessorWidget(
        extensions=extensions, get_filter_value=pd.Series([2, 3, 4], dtype=np.float64)
    )

    # Raises for non-numeric numpy array
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions, get_filter_value=np.array(["2", "3", "4"])
        )

    # Accept 2D numpy arrays where the second dimension is 1
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=np.array([2, 3, 4], dtype=np.float32).reshape(-1, 1),
    )

    # Raises for 2D numpy array with second dim >1
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions,
            get_filter_value=np.array([2, 3, 4, 6, 7, 8], dtype=np.float32).reshape(
                -1, 2
            ),
        )

    # Must be floating-point pyarrow array type
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions,
            get_filter_value=pa.array(np.array([2, 3, 4], dtype=np.int64)),
        )

    # Accept floating point pyarrow arrays
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=pa.array(np.array([2, 3, 4], dtype=np.float32)),
    )
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=pa.array(np.array([2, 3, 4], dtype=np.float64)),
    )


def test_filter_value_validation_filter_size_3():
    extensions = [DataFilterExtension(filter_size=3)]

    # Must pass a value
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=())

    # Strings not allowed
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value="2")

    # Lists and tuples must match filter_size
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=[1, 2])
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=(1, 2))
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=[1, 2, 3])
    FilterValueAccessorWidget(extensions=extensions, get_filter_value=(1, 2, 3))

    # Disallow floats and ints
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=2)
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(extensions=extensions, get_filter_value=2.0)

    # Numpy arrays
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions, get_filter_value=np.array([2, 3, 4])
        )
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=np.array(
            [1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.float32
        ).reshape(-1, 3),
    )
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=np.array(
            [1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.float64
        ).reshape(-1, 3),
    )

    # Disallow pandas series
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions, get_filter_value=pd.Series([2, 3, 4])
        )

    # Raises for non-numeric numpy array
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions, get_filter_value=np.array(["2", "3", "4"])
        )

    # Disallow 2D numpy arrays where the second dimension is 1
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions,
            get_filter_value=np.array([2, 3, 4], dtype=np.float32).reshape(-1, 1),
        )

    # Must be floating-point pyarrow array type
    with pytest.raises(TraitError):
        FilterValueAccessorWidget(
            extensions=extensions,
            get_filter_value=pa.FixedSizeListArray.from_arrays(
                np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.int64), 3
            ),
        )

    # Accept floating point pyarrow arrays
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=pa.FixedSizeListArray.from_arrays(
            np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.float32), 3
        ),
    )
    FilterValueAccessorWidget(
        extensions=extensions,
        get_filter_value=pa.FixedSizeListArray.from_arrays(
            np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.float64), 3
        ),
    )


class NormalAccessorWidget(BaseLayer):
    _rows_per_chunk = 2

    table = pa.table({"data": [1, 2, 3]})

    value = NormalAccessor()


def test_normal_accessor_validation_list_length():
    with pytest.raises(TraitError, match="normal scalar to have length 3"):
        NormalAccessorWidget(value=(1, 2))

    with pytest.raises(TraitError, match="normal scalar to have length 3"):
        NormalAccessorWidget(value=(1, 2, 3, 4))

    NormalAccessorWidget(value=(1, 2, 3))


def test_normal_accessor_validation_list_type():
    # tuple or list must be of scalar type
    with pytest.raises(
        TraitError, match="all elements of normal scalar to be int or float type"
    ):
        NormalAccessorWidget(value=["1.1", 2.2, 3.3])


def test_normal_accessor_validation_dim_shape_np_arr():
    arr_size3 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9]).reshape(-1, 3)
    arr_size2 = np.array([1, 2, 3, 4, 5, 6]).reshape(-1, 2)

    NormalAccessorWidget(value=arr_size3)

    with pytest.raises(TraitError, match="normal array to be 2D with shape"):
        NormalAccessorWidget(value=arr_size2)


def test_normal_accessor_validation_np_dtype():
    arr_size3_int = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9]).reshape(-1, 3)
    arr_size3_float = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.float64).reshape(
        -1, 3
    )

    NormalAccessorWidget(value=arr_size3_int)
    NormalAccessorWidget(value=arr_size3_float)

    arr_size3_str = np.array(["1", "2", "3", "4", "5", "6", "7", "8", "9"]).reshape(
        -1, 3
    )

    # acceptable data types within a numpy array are float32
    with pytest.raises(TraitError, match="expected normal array to have numeric type"):
        NormalAccessorWidget(value=arr_size3_str)


def test_normal_accessor_validation_pyarrow_array_type():
    # array type must be FixedSizeList, of length 3, of float32 type
    with pytest.raises(
        TraitError, match="expected normal pyarrow array to be a FixedSizeList"
    ):
        NormalAccessorWidget(value=pa.array(np.array([1, 2, 3], dtype=np.float64)))

    np_arr = np.array([1, 2, 3], dtype=np.float32).repeat(3, axis=0)
    NormalAccessorWidget(value=pa.FixedSizeListArray.from_arrays(np_arr, 3))

    np_arr = np.array([1, 2, 3], dtype=np.float64).repeat(3, axis=0)
    NormalAccessorWidget(value=pa.FixedSizeListArray.from_arrays(np_arr, 3))

    np_arr = np.array([1, 2, 3], dtype=np.uint8).repeat(3, axis=0)
    with pytest.raises(
        TraitError, match="expected pyarrow array to be floating point type"
    ):
        NormalAccessorWidget(value=pa.FixedSizeListArray.from_arrays(np_arr, 3))

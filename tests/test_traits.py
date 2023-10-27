import numpy as np
import pyarrow as pa
import pytest
from ipywidgets import Widget
from traitlets import TraitError

from lonboard.traits import ColorAccessor, FloatAccessor


class ColorAccessorWidget(Widget):
    _rows_per_chunk = 2

    color = ColorAccessor()


def test_color_accessor_validation_list_length():
    # tuple or list must have 3 or 4 elements
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=())

    with pytest.raises(TraitError):
        ColorAccessorWidget(color=(1, 2))

    with pytest.raises(TraitError):
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

    ColorAccessorWidget(color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 3))
    ColorAccessorWidget(color=np.array([1, 2, 3, 255], dtype=np.uint8).reshape(-1, 4))


def test_color_accessor_validation_np_dtype():
    # must be np.uint8
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=np.array([1, 2, 3]).reshape(-1, 3))

    ColorAccessorWidget(color=np.array([1, 2, 3], dtype=np.uint8).reshape(-1, 3))


def test_color_accessor_validation_pyarrow_array_type():
    # array type must be FixedSizeList
    with pytest.raises(TraitError):
        ColorAccessorWidget(color=pa.array(np.array([1, 2, 3], dtype=np.float64)))

    np_arr = np.array([1, 2, 3], dtype=np.uint8)
    ColorAccessorWidget(color=pa.FixedSizeListArray.from_arrays(np_arr, 3))

    np_arr = np.array([1, 2, 3, 255], dtype=np.uint8)
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


class FloatAccessorWidget(Widget):
    _rows_per_chunk = 2

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

    # Must be floating-point array type
    with pytest.raises(TraitError):
        FloatAccessorWidget(value=pa.array(np.array([2, 3, 4])))

    FloatAccessorWidget(value=pa.array(np.array([2, 3, 4], dtype=np.float32)))
    FloatAccessorWidget(value=pa.array(np.array([2, 3, 4], dtype=np.float64)))

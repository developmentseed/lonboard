import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from traitlets.traitlets import TraitError

from lonboard.layer import BaseLayer
from lonboard.traits import H3Accessor

VALID_INDICES = np.array(
    [
        0x8075FFFFFFFFFFF,
        0x81757FFFFFFFFFF,
        0x82754FFFFFFFFFF,
    ],
    dtype=np.uint64,
)

HEX_STRINGS = [f"{v:x}" for v in VALID_INDICES]


class H3AccessorWidget(BaseLayer):
    _rows_per_chunk = 2

    # Any tests that are intended to pass validation checks must also have 3 rows, since
    # there's another length check in the serialization code.
    table = pa.table({"data": [1, 2, 3]})

    get_hexagon = H3Accessor()


def test_pandas_series_str():
    str_series = pd.Series(HEX_STRINGS)
    H3AccessorWidget(get_hexagon=str_series)


def test_pandas_series_uint64():
    uint_series = pd.Series(VALID_INDICES)
    H3AccessorWidget(get_hexagon=uint_series)


def test_pandas_series_str_invalid_length():
    str_series = pd.Series(["abc", "defg", "hijklmnop"])
    with pytest.raises(TraitError, match="not all 15 characters long"):
        H3AccessorWidget(get_hexagon=str_series)


def test_pandas_u8():
    uint8_array = np.array([1, 2, 3], dtype=np.uint8)
    with pytest.raises(
        TraitError,
        match="numpy array not object, str, or uint64 dtype",
    ):
        H3AccessorWidget(get_hexagon=uint8_array)


def test_numpy_s15():
    str_array = np.array(HEX_STRINGS, dtype="S15")
    H3AccessorWidget(get_hexagon=str_array)


def test_numpy_str_object():
    str_array = np.array(HEX_STRINGS, dtype=np.object_)
    H3AccessorWidget(get_hexagon=str_array)


def test_numpy_uint64():
    H3AccessorWidget(get_hexagon=VALID_INDICES)


def test_numpy_uint8():
    uint8_array = np.array([1, 2, 3], dtype=np.uint8)
    with pytest.raises(
        TraitError,
        match="numpy array not object, str, or uint64 dtype",
    ):
        H3AccessorWidget(get_hexagon=uint8_array)


def test_arrow_string_array():
    str_array = pa.array(HEX_STRINGS, type=pa.string())
    H3AccessorWidget(get_hexagon=str_array)

    str_array = pa.array(HEX_STRINGS, type=pa.large_string())
    H3AccessorWidget(get_hexagon=str_array)

    str_array = pa.array(HEX_STRINGS, type=pa.string_view())
    H3AccessorWidget(get_hexagon=str_array)


def test_arrow_uint64_array():
    uint64_array = pa.array(VALID_INDICES, type=pa.uint64())
    H3AccessorWidget(get_hexagon=uint64_array)

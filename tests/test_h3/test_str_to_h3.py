"""Tests for str_to_h3 conversion."""

import h3.api.numpy_int as h3
import numpy as np

from lonboard._h3 import h3_to_str, str_to_h3

H3_INTEGERS = np.array(
    [
        0x8075FFFFFFFFFFF,
        0x81757FFFFFFFFFF,
        0x82754FFFFFFFFFF,
        0x83754EFFFFFFFFF,
        0x84754A9FFFFFFFF,
        0x85754E67FFFFFFF,
        0x86754E64FFFFFFF,
        0x87754E64DFFFFFF,
        0x88754E6499FFFFF,
        0x89754E64993FFFF,
        0x8A754E64992FFFF,
        0x8B754E649929FFF,
        0x8C754E649929DFF,
        0x8D754E64992D6FF,
        0x8E754E64992D6DF,
        0x8F754E64992D6D8,
    ],
    dtype=np.uint64,
)
H3_HEX_STRINGS = [h3.int_to_str(v) for v in H3_INTEGERS]


def test_str_to_h3_roundtrip():
    """Test that str_to_h3 correctly converts hex strings back to uint64."""
    # Convert to strings and back
    hex_strings = h3_to_str(H3_INTEGERS)
    assert [bytes(x).decode() for x in hex_strings] == H3_HEX_STRINGS

    back = str_to_h3(hex_strings)

    np.testing.assert_array_equal(back, H3_INTEGERS)


def test_str_to_h3_single():
    """Test single hex string conversion."""
    hex_strings = np.array(["8075FFFFFFFFFFF"], dtype="S15")
    result = str_to_h3(hex_strings)
    expected = np.array([0x8075FFFFFFFFFFF], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)


def test_str_to_h3_lowercase():
    """Test that lowercase hex strings work."""
    hex_strings = np.array(["8075fffffffffff"], dtype="S15")
    result = str_to_h3(hex_strings)
    expected = np.array([0x8075FFFFFFFFFFF], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)


def test_str_to_h3_mixed_case():
    """Test that mixed case hex strings work."""
    hex_strings = np.array(["8075fFfFfFfFfFf"], dtype="S15")
    result = str_to_h3(hex_strings)
    expected = np.array([0x8075FFFFFFFFFFF], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)


def test_str_to_h3_empty():
    """Test empty array handling."""
    hex_strings = np.array([], dtype=np.str_)
    result = str_to_h3(hex_strings)
    expected = np.array([], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)


def test_str_to_h3_zeros():
    """Test conversion of zeros."""
    hex_strings = np.array(["000000000000000"], dtype=np.str_)
    result = str_to_h3(hex_strings)
    expected = np.array([0x0], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)


def test_str_to_h3_max_value():
    """Test conversion of maximum uint64 value."""
    hex_strings = np.array(["FFFFFFFFFFFFFFF"], dtype=np.str_)
    result = str_to_h3(hex_strings)
    expected = np.array([0xFFFFFFFFFFFFFFF], dtype=np.uint64)

    np.testing.assert_array_equal(result, expected)

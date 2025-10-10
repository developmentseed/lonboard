"""Vendor h3o cell index tests

https://github.com/HydroniumLabs/h3o/blob/6918ea071cf2d65a20cbb103f32d984a01161819/tests/h3/is_valid_cell.rs
"""

import h3.api.numpy_int as h3
import numpy as np
import pytest

from lonboard._h3 import validate_h3_indices

VALID_INDICES = np.array(
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


def test_valid_indices():
    for cell in VALID_INDICES:
        assert h3.is_valid_cell(cell)
    validate_h3_indices(VALID_INDICES)


def test_invalid_high_bit_set():
    h3_indices = np.array([0x88C2BAE305336BFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Tainted reserved bits in indices"):
        validate_h3_indices(h3_indices)


def test_invalid_mode():
    h3_indices = np.array([0x28C2BAE305336BFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Invalid index mode in indices"):
        validate_h3_indices(h3_indices)


def test_tainted_reserved_bits():
    h3_indices = np.array([0xAC2BAE305336BFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Tainted reserved bits in indices"):
        validate_h3_indices(h3_indices)


def test_invalid_base_cell():
    h3_indices = np.array([0x80FFFFFFFFFFFFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Invalid base cell in indices"):
        validate_h3_indices(h3_indices)


def test_unexpected_unused_first():
    h3_indices = np.array([0x8C2BEE305336BFFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Tainted reserved bits in indices"):
        validate_h3_indices(h3_indices)


def test_unexpected_unused_middle():
    h3_indices = np.array([0x8C2BAE33D336BFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Unexpected unused direction in indices"):
        validate_h3_indices(h3_indices)


def test_unexpected_unused_last():
    h3_indices = np.array([0x8C2BAE305336FFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Unexpected unused direction in indices"):
        validate_h3_indices(h3_indices)


def test_missing_unused_first():
    h3_indices = np.array([0x8C0FAE305336AFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Invalid unused direction pattern in indices"):
        validate_h3_indices(h3_indices)


def test_missing_unused_middle():
    h3_indices = np.array([0x8C0FAE305336FEF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Invalid unused direction pattern in indices"):
        validate_h3_indices(h3_indices)


def test_missing_unused_last():
    h3_indices = np.array([0x81757FFFFFFFFFE], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(ValueError, match="Invalid unused direction pattern in indices"):
        validate_h3_indices(h3_indices)


def test_deleted_subsequence_hexagon1():
    h3_indices = np.array([0x81887FFFFFFFFFF], dtype=np.uint64)
    assert h3.is_valid_cell(h3_indices[0])
    validate_h3_indices(h3_indices)


def test_deleted_subsequence_pentagon1():
    h3_indices = np.array([0x81087FFFFFFFFFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(
        ValueError,
        match="Pentagonal cell index with a deleted subsequence",
    ):
        validate_h3_indices(h3_indices)


def test_deleted_subsequence_hexagon2():
    h3_indices = np.array([0x8804000011FFFFF], dtype=np.uint64)
    assert h3.is_valid_cell(h3_indices[0])
    validate_h3_indices(h3_indices)


def test_deleted_subsequence_pentagon2():
    h3_indices = np.array([0x8808000011FFFFF], dtype=np.uint64)
    assert not h3.is_valid_cell(h3_indices[0])
    with pytest.raises(
        ValueError,
        match="Pentagonal cell index with a deleted subsequence",
    ):
        validate_h3_indices(h3_indices)

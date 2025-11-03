"""Implement h3 cell validation in pure numpy.

It's hard to surface errors from deck.gl back to Python, so it's a bad user experience
if the JS console errors and silently nothing renders. But also I don't want to depend
on the h3 library for this because the h3 library isn't vectorized (arghhhh!) and I
don't want to require the dependency.

So instead, I spend my time porting code into Numpy 😄.

Ported from Rust code in h3o:

https://github.com/HydroniumLabs/h3o/blob/07dcb85d9cb539f685ec63050ef0954b1d9f3864/src/index/cell.rs#L1897-L1962
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = ["validate_h3_indices"]

MODE_OFFSET = 59
"""Offset (in bits) of the mode in an H3 index."""

MODE_MASK = 0b1111 << MODE_OFFSET

EDGE_OFFSET = 56
"""Offset (in bits) of the cell edge in an H3 index."""

EDGE_MASK = 0b111 << EDGE_OFFSET

VERTEX_OFFSET = 56
"""Offset (in bits) of the cell vertex in an H3 index."""

VERTEX_MASK = 0b111 << VERTEX_OFFSET

DIRECTIONS_MASK = 0x0000_1FFF_FFFF_FFFF
"""Bitmask to select the directions bits in an H3 index."""

INDEX_MODE_CELL = 1
"""H3 index mode for cells."""

BASE_CELL_OFFSET = 45
"""Offset (in bits) of the base cell in an H3 index."""

BASE_CELL_MASK = 0b111_1111 << BASE_CELL_OFFSET
"""Bitmask to select the base cell bits in an H3 index."""

MAX_BASE_CELL = 121
"""Maximum value for a base cell."""

RESOLUTION_OFFSET = 52
"""The bit offset of the resolution in an H3 index."""

RESOLUTION_MASK = 0b1111 << RESOLUTION_OFFSET
"""Bitmask to select the resolution bits in an H3 index."""

MAX_RESOLUTION = 15
"""Maximum supported H3 resolution."""

DIRECTION_BITSIZE = 3
"""Size, in bits, of a direction (range [0; 6])."""

BASE_PENTAGONS_HI = 0x0020_0802_0008_0100
"""Bitmap where a bit's position represents a base cell value (high part).

Refactored from upstream 128 bit integer
https://github.com/HydroniumLabs/h3o/blob/3b40550291a57552117c48c19841557a3b0431e1/src/base_cell.rs#L12
"""

BASE_PENTAGONS_LO = 0x8402_0040_0100_4010
"""Bitmap where a bit's position represents a base cell value (low part).

Refactored from upstream 128 bit integer
https://github.com/HydroniumLabs/h3o/blob/3b40550291a57552117c48c19841557a3b0431e1/src/base_cell.rs#L12
"""

PENTAGON_BASE_CELLS = np.array(
    [4, 14, 24, 33, 38, 49, 58, 63, 72, 83, 97, 107],
    dtype=np.uint8,
)
"""Set of pentagon base cells."""


def validate_h3_indices(h3_indices: NDArray[np.uint64]) -> None:
    """Validate an array of uint64 H3 indices.

    Raises ValueError if any index is invalid.
    """
    invalid_reserved_bits = h3_indices >> 56 & 0b1000_0111 != 0
    bad_indices = np.where(invalid_reserved_bits)[0]
    if len(bad_indices) > 0:
        raise ValueError(
            f"Tainted reserved bits in indices: {bad_indices.tolist()}\n"
            f"with values {h3_indices[bad_indices].tolist()}",
        )

    invalid_mode = get_mode(h3_indices) != INDEX_MODE_CELL
    bad_indices = np.where(invalid_mode)[0]
    if len(bad_indices) > 0:
        raise ValueError(
            f"Invalid index mode in indices: {bad_indices.tolist()}",
            f"with values {h3_indices[bad_indices].tolist()}",
        )

    base = get_base_cell(h3_indices)
    invalid_base_cell = base > MAX_BASE_CELL
    bad_indices = np.where(invalid_base_cell)[0]
    if len(bad_indices) > 0:
        raise ValueError(
            f"Invalid base cell in indices: {bad_indices.tolist()}",
            f"with values {h3_indices[bad_indices].tolist()}",
        )

    # Resolution is always valid: coded on 4 bits, valid range is [0; 15].
    resolution = get_resolution(h3_indices)

    # Check that we have a tail of unused cells  after `resolution` cells.
    #
    # We expect every bit to be 1 in the tail (because unused cells are
    # represented by `0b111`), i.e. every bit set to 0 after a NOT.
    unused_count = MAX_RESOLUTION - resolution
    unused_bitsize = unused_count * DIRECTION_BITSIZE
    unused_mask = (1 << unused_bitsize.astype(np.uint64)) - 1
    invalid_unused_direction_pattern = (~h3_indices) & unused_mask != 0
    bad_indices = np.where(invalid_unused_direction_pattern)[0]
    if len(bad_indices) > 0:
        raise ValueError(
            f"Invalid unused direction pattern in indices: {bad_indices.tolist()}",
            f"with values {h3_indices[bad_indices].tolist()}",
        )

    # Check that we have `resolution` valid cells (no unused ones).
    dirs_mask = (1 << (resolution * DIRECTION_BITSIZE).astype(np.uint64)) - 1
    dirs = (h3_indices >> unused_bitsize) & dirs_mask
    invalid_unused_direction = has_unused_direction(dirs)
    bad_indices = np.where(invalid_unused_direction)[0]
    if len(bad_indices) > 0:
        raise ValueError(
            f"Unexpected unused direction in indices: {bad_indices.tolist()}",
            f"with values {h3_indices[bad_indices].tolist()}",
        )

    # Check for pentagons with deleted subsequence.
    has_pentagon_base = np.logical_and(is_pentagon(base), resolution != 0)
    pentagon_base_indices = np.where(has_pentagon_base)[0]
    if len(pentagon_base_indices) > 0:
        pentagons = h3_indices[pentagon_base_indices]
        pentagon_resolutions = resolution[pentagon_base_indices]
        pentagon_dirs = dirs[pentagon_base_indices]

        # Move directions to the front, so that we can count leading zeroes.
        pentagon_offset = 64 - (pentagon_resolutions * DIRECTION_BITSIZE)

        # NOTE: The following was ported via GPT from Rust `leading_zeros`
        # https://github.com/HydroniumLabs/h3o/blob/07dcb85d9cb539f685ec63050ef0954b1d9f3864/src/index/cell.rs#L1951

        # Find the position of the first bit set, if it's a multiple of 3
        # that means we have a K axe as the first non-center direction,
        # which is forbidden.
        shifted = pentagon_dirs << pentagon_offset

        # Compute leading zeros for each element (assuming 64-bit unsigned integers)
        # where `leading_zeros = 64 - shifted.bit_length()`
        # numpy doesn't have bit_length, so use log2 and handle zeros
        bitlen = np.where(shifted == 0, 0, np.floor(np.log2(shifted)).astype(int) + 1)
        leading_zeros = 64 - bitlen

        # Add 1 and check if multiple of 3
        is_multiple_of_3 = ((leading_zeros + 1) % 3) == 0
        bad_indices = np.where(is_multiple_of_3)[0]
        if len(bad_indices) > 0:
            raise ValueError(
                f"Pentagonal cell index with a deleted subsequence: {bad_indices.tolist()}",
                f"with values {pentagons[bad_indices].tolist()}",
            )


def get_mode(bits: NDArray[np.uint64]) -> NDArray[np.uint8]:
    """Return the H3 index mode bits."""
    return ((bits & MODE_MASK) >> MODE_OFFSET).astype(np.uint8)


def get_base_cell(bits: NDArray[np.uint64]) -> NDArray[np.uint8]:
    """Return the H3 index base cell bits."""
    return ((bits & BASE_CELL_MASK) >> BASE_CELL_OFFSET).astype(np.uint8)


def get_resolution(bits: NDArray[np.uint64]) -> NDArray[np.uint8]:
    """Return the H3 index resolution."""
    return ((bits & RESOLUTION_MASK) >> RESOLUTION_OFFSET).astype(np.uint8)


def has_unused_direction(dirs: NDArray) -> NDArray[np.bool_]:
    """Check if there is at least one unused direction in the given directions.

    Copied from upstream
    https://github.com/HydroniumLabs/h3o/blob/07dcb85d9cb539f685ec63050ef0954b1d9f3864/src/index/cell.rs#L2056-L2107
    """
    LO_MAGIC = 0b001_001_001_001_001_001_001_001_001_001_001_001_001_001_001  # noqa: N806
    HI_MAGIC = 0b100_100_100_100_100_100_100_100_100_100_100_100_100_100_100  # noqa: N806

    return ((~dirs - LO_MAGIC) & (dirs & HI_MAGIC)) != 0


def is_pentagon(cell: NDArray[np.uint8]) -> NDArray[np.bool_]:
    """Return true if the base cell is pentagonal.

    Note that this is **not** copied from the upstream:
    https://github.com/HydroniumLabs/h3o/blob/3b40550291a57552117c48c19841557a3b0431e1/src/base_cell.rs#L33-L47

    Because they use a 128 bit integer as a bitmap, which is not available in
    numpy. Instead we use a simple lookup in a static array.
    """
    return np.isin(cell, PENTAGON_BASE_CELLS)

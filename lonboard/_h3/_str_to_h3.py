from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def str_to_h3(hex_arr: NDArray[np.str_]) -> NDArray[np.uint64]:
    """Convert an array of hexadecimal strings to H3 indices (uint64).

    This is a pure NumPy vectorized implementation that processes hex strings
    character by character without Python loops.

    Args:
        hex_arr: Array of hexadecimal strings (15 characters each)

    Returns:
        Array of H3 indices as uint64 integers

    """
    if len(hex_arr) == 0:
        return np.array([], dtype=np.uint64)

    # Convert to S15 fixed-width byte strings if needed
    # View as 2D array of individual bytes (shape: n x 15)
    hex_bytes = np.asarray(hex_arr, dtype="S15").view("S1").reshape(len(hex_arr), -1)

    # Convert ASCII bytes to numeric values
    # Get the ASCII code of each character
    ascii_vals = hex_bytes.view(np.uint8)

    # Convert hex ASCII to numeric values (0-15)
    # '0'-'9' (48-57) -> 0-9
    # 'A'-'F' (65-70) -> 10-15
    # 'a'-'f' (97-102) -> 10-15
    vals = ascii_vals - ord("0")  # Shift '0' to 0
    vals = np.where(vals > 9, vals - 7, vals)  # 'A'=65-48=17 -> 17-7=10
    vals = np.where(vals > 15, vals - 32, vals)  # 'a'=97-48=49 -> 49-7=42 -> 42-32=10

    # Create powers of 16 for each position (most significant first)
    # For 15 hex digits: [16^14, 16^13, ..., 16^1, 16^0]
    n_digits = hex_bytes.shape[1]
    powers = 16 ** np.arange(n_digits - 1, -1, -1, dtype=np.uint64)

    # Compute dot product to get final uint64 values
    # Each row: sum(digit_i * 16^(n-1-i))
    return np.dot(vals.astype(np.uint64), powers)

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# ruff: noqa: ERA001


def str_to_h3(hex_arr: NDArray[np.str_]) -> NDArray[np.uint64]:
    return np.array([int(h, 16) for h in hex_arr])


# # Convert ASCII bytes to numeric nibble values
# vals = np.frombuffer(hex_arr, dtype=np.uint8).reshape(len(hex_arr), -1)

# # Convert ASCII hex chars to 0-15
# nibbles = (vals - ord("0")).astype(np.int8)
# nibbles[nibbles > 9] -= 39  # 'a' - '0' = 49, adjust so 'a'→10, 'f'→15

# # Accumulate nibbles into integer
# # Each hex digit represents 4 bits
# ints = nibbles[:, 0] << 60
# for i in range(1, 16):
#     ints |= nibbles[:, i].astype(np.uint64) << (60 - 4 * i)

# pass


# print(ints)
# # [10, 255, 3735928559]


# pass
# # Example 2D S1 array of hex chars (shape: n x 15)
# arr_s1 = np.array([list(b"00000000000000A"), list(b"0000000000000FF")], dtype="S1")

# n_rows, n_cols = arr_s1.shape
# assert n_cols == 15, "Each hex string must be exactly 15 characters"

# # Step 1: convert ASCII bytes to numeric values 0-15
# arr_int = arr_s1.view("uint8")  # get ASCII code
# # '0'-'9' -> 0-9, 'A'-'F' -> 10-15
# arr_val = arr_int.copy()
# arr_val = np.where(arr_val >= ord("0"), arr_val - ord("0"), arr_val)
# arr_val = np.where(arr_val >= 10, arr_val - 7, arr_val)  # adjust 'A'-'F'

# # Step 2: create powers of 16 for each position
# powers = 16 ** np.arange(n_cols - 1, -1, -1, dtype=np.uint64)

# # Step 3: compute dot product along each row
# uint64_arr = np.dot(arr_val, powers)

# print(uint64_arr)
# # Output: [10 255]

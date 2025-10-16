from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arro3.core import Table

# Target chunk size for Arrow (uncompressed) per Parquet chunk
DEFAULT_ARROW_CHUNK_BYTES_SIZE = 5 * 1024 * 1024  # 5MB

# Maximum number of separate chunks/row groups to allow splitting an input layer into
# Deck.gl can pick from a maximum of 256 layers, and a user could have many layers, so
# we don't want to use too many layers per data file.
DEFAULT_MAX_NUM_CHUNKS = 32


def infer_rows_per_chunk(table: Table) -> int:
    # At least one chunk
    num_chunks = max(round(table.nbytes / DEFAULT_ARROW_CHUNK_BYTES_SIZE), 1)

    # Clamp to the maximum number of chunks
    num_chunks = min(num_chunks, DEFAULT_MAX_NUM_CHUNKS)

    return math.ceil(table.num_rows / num_chunks)

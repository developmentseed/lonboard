import numpy as np
from arro3.core import Array, ChunkedArray, Table


def add_positional_row_index(
    table: Table,
) -> Table:
    num_rows = table.num_rows
    if num_rows <= np.iinfo(np.uint8).max:
        arange_col = Array(np.arange(num_rows, dtype=np.uint8))
    elif num_rows <= np.iinfo(np.uint16).max:
        arange_col = Array(np.arange(num_rows, dtype=np.uint16))
    elif num_rows <= np.iinfo(np.uint32).max:
        arange_col = Array(np.arange(num_rows, dtype=np.uint32))
    else:
        arange_col = Array(np.arange(num_rows, dtype=np.uint64))

    return table.append_column("row_index", ChunkedArray([arange_col]))

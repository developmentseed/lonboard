from io import BytesIO
from typing import List, Tuple, Union

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.typing import NDArray

DEFAULT_PARQUET_COMPRESSION = "ZSTD"
DEFAULT_PARQUET_COMPRESSION_LEVEL = 7


def serialize_parquet(table: pa.Table) -> bytes:
    with BytesIO() as bio:
        # TODO: careful about row group size
        pq.write_table(
            table,
            bio,
            compression=DEFAULT_PARQUET_COMPRESSION,
            compression_level=DEFAULT_PARQUET_COMPRESSION_LEVEL,
        )
        return bio.getvalue()


def serialize_color_ndarray(data: NDArray[np.uint8]) -> bytes:
    assert np.issubdtype(data.dtype, np.uint8), "Color array must be uint8 type."
    assert data.ndim == 2, "Color array must be 2D."

    list_size = data.shape[1]
    assert list_size in (3, 4), "Color array must have 3 or 4 as its second dimension."

    pyarrow_arr = pa.FixedSizeListArray.from_arrays(data.flatten("C"), list_size)
    pyarrow_table = pa.table({"color": pyarrow_arr})
    return serialize_parquet(pyarrow_table)


def serialize_color_accessor(
    data: Union[List[int], Tuple[int], NDArray[np.uint8]], obj=None
):
    # print(obj)
    # print(type(obj))
    if data is None:
        return None

    if isinstance(data, np.ndarray):
        return serialize_color_ndarray(data)

    return data


COLOR_SERIALIZATION = {"to_json": serialize_color_accessor}

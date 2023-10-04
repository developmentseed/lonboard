from io import BytesIO
from typing import List, Tuple, Union

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.typing import NDArray

DEFAULT_PARQUET_COMPRESSION = "ZSTD"
DEFAULT_PARQUET_COMPRESSION_LEVEL = 7
DEFAULT_PARQUET_CHUNK_SIZE = 2**16


def serialize_table_to_parquet(table: pa.Table) -> bytes:
    with BytesIO() as bio:
        # NOTE: careful about row group size; needs to be always constant
        pq.write_table(
            table,
            bio,
            row_group_size=DEFAULT_PARQUET_CHUNK_SIZE,
            compression=DEFAULT_PARQUET_COMPRESSION,
            compression_level=DEFAULT_PARQUET_COMPRESSION_LEVEL,
        )
        return bio.getvalue()


def color_ndarray_to_pyarrow(data: NDArray[np.uint8]) -> pa.FixedSizeListArray:
    assert np.issubdtype(data.dtype, np.uint8), "Color array must be uint8 type."
    assert data.ndim == 2, "Color array must be 2D."

    list_size = data.shape[1]
    assert list_size in (3, 4), "Color array must have 3 or 4 as its second dimension."

    return pa.FixedSizeListArray.from_arrays(data.flatten("C"), list_size)


def serialize_pyarrow_color(data: pa.FixedSizeListArray) -> bytes:
    pyarrow_table = pa.table({"color": data})
    return serialize_table_to_parquet(pyarrow_table)


def serialize_color_accessor(
    data: Union[List[int], Tuple[int], NDArray[np.uint8]], obj=None
):
    if data is None:
        return None

    if isinstance(data, np.ndarray):
        parr = color_ndarray_to_pyarrow(data)
        return serialize_pyarrow_color(parr)

    if isinstance(data, (pa.ChunkedArray, pa.Array)):
        assert pa.types.is_fixed_size_list(data.type)
        assert data.type.list_size in (3, 4)
        return serialize_pyarrow_color(data)

    return data


def serialize_pyarrow_value_column(data: pa.Array) -> bytes:
    pyarrow_table = pa.table({"value": data})
    return serialize_table_to_parquet(pyarrow_table)


def serialize_float_accessor(data: Union[int, float, NDArray[np.floating]], obj=None):
    if data is None:
        return None

    if isinstance(data, np.ndarray):
        assert np.issubdtype(data.dtype, np.number), "Expected numeric dtype"
        # TODO: should we always be casting to float32? Should it be possible/allowed to
        # pass in ~int8 or a data type smaller than float32?
        parr = pa.array(data.astype(np.float32))
        return serialize_pyarrow_value_column(parr)

    if isinstance(data, (pa.ChunkedArray, pa.Array)):
        assert pa.types.is_floating(data.type)
        return serialize_pyarrow_value_column(data.cast(pa.float32()))

    return data


COLOR_SERIALIZATION = {"to_json": serialize_color_accessor}
FLOAT_SERIALIZATION = {"to_json": serialize_float_accessor}

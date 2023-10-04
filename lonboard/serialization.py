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


def serialize_pyarrow_column(data: pa.Array) -> bytes:
    """Serialize a pyarrow column to a Parquet file with one column"""
    pyarrow_table = pa.table({"value": data})
    return serialize_table_to_parquet(pyarrow_table)


def serialize_color_accessor(
    data: Union[List[int], Tuple[int], NDArray[np.uint8]], obj=None
):
    if data is None:
        return None

    if isinstance(data, (list, tuple)):
        return data

    assert isinstance(data, (pa.ChunkedArray, pa.Array))
    return serialize_pyarrow_column(data)


def serialize_float_accessor(data: Union[int, float, NDArray[np.floating]], obj=None):
    if data is None:
        return None

    if isinstance(data, (int, float)):
        return data

    assert isinstance(data, (pa.ChunkedArray, pa.Array))
    return serialize_pyarrow_column(data)


def serialize_table(data, obj=None):
    assert isinstance(data, pa.Table), "expected pyarrow table"
    return serialize_table_to_parquet(data)


COLOR_SERIALIZATION = {"to_json": serialize_color_accessor}
FLOAT_SERIALIZATION = {"to_json": serialize_float_accessor}
TABLE_SERIALIZATION = {"to_json": serialize_table}

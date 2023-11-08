import math
from io import BytesIO
from typing import List, Tuple, Union

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.typing import NDArray

DEFAULT_PARQUET_COMPRESSION = "ZSTD"
DEFAULT_PARQUET_COMPRESSION_LEVEL = 7
DEFAULT_PARQUET_CHUNK_SIZE = 2**16
# Target chunk size for Arrow (uncompressed) per Parquet chunk
DEFAULT_ARROW_CHUNK_BYTES_SIZE = 5 * 1024 * 1024  # 5MB


def serialize_table_to_parquet(
    table: pa.Table, *, max_chunksize: int = DEFAULT_PARQUET_CHUNK_SIZE
) -> List[bytes]:
    buffers: List[bytes] = []
    for record_batch in table.to_batches(max_chunksize=max_chunksize):
        with BytesIO() as bio:
            with pq.ParquetWriter(
                bio,
                schema=table.schema,
                compression=DEFAULT_PARQUET_COMPRESSION,
                compression_level=DEFAULT_PARQUET_COMPRESSION_LEVEL,
            ) as writer:
                writer.write_batch(record_batch, row_group_size=record_batch.num_rows)

            buffers.append(bio.getvalue())

    return buffers


def serialize_pyarrow_column(data: pa.Array, *, max_chunksize: int) -> List[bytes]:
    """Serialize a pyarrow column to a Parquet file with one column"""
    pyarrow_table = pa.table({"value": data})
    return serialize_table_to_parquet(pyarrow_table, max_chunksize=max_chunksize)


def serialize_color_accessor(
    data: Union[List[int], Tuple[int], NDArray[np.uint8]], obj
):
    if data is None:
        return None

    if isinstance(data, (list, tuple)):
        return data

    assert isinstance(data, (pa.ChunkedArray, pa.Array))
    return serialize_pyarrow_column(data, max_chunksize=obj._rows_per_chunk)


def serialize_float_accessor(data: Union[int, float, NDArray[np.floating]], obj):
    if data is None:
        return None

    if isinstance(data, (str, int, float)):
        return data

    assert isinstance(data, (pa.ChunkedArray, pa.Array))
    return serialize_pyarrow_column(data, max_chunksize=obj._rows_per_chunk)


def serialize_table(data, obj):
    assert isinstance(data, pa.Table), "expected pyarrow table"
    return serialize_table_to_parquet(data, max_chunksize=obj._rows_per_chunk)


def infer_rows_per_chunk(table: pa.Table) -> int:
    num_chunks = max(round(table.nbytes / DEFAULT_ARROW_CHUNK_BYTES_SIZE), 1)
    rows_per_chunk = math.ceil((table.num_rows / num_chunks))
    return rows_per_chunk


COLOR_SERIALIZATION = {"to_json": serialize_color_accessor}
# TODO: rename as it's used for text as well
FLOAT_SERIALIZATION = {"to_json": serialize_float_accessor}
TABLE_SERIALIZATION = {"to_json": serialize_table}

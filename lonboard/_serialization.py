from __future__ import annotations

import math
from io import BytesIO
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import numpy as np
from arro3.core import Array, ChunkedArray, RecordBatch, Table
from traitlets import TraitError

from lonboard.models import ViewState

if TYPE_CHECKING:
    from numpy.typing import NDArray


DEFAULT_PARQUET_COMPRESSION = "ZSTD"
DEFAULT_PARQUET_COMPRESSION_LEVEL = 7
DEFAULT_PARQUET_CHUNK_SIZE = 2**16
# Target chunk size for Arrow (uncompressed) per Parquet chunk
DEFAULT_ARROW_CHUNK_BYTES_SIZE = 5 * 1024 * 1024  # 5MB

# Maximum number of separate chunks/row groups to allow splitting an input layer into
# Deck.gl can pick from a maximum of 256 layers, and a user could have many layers, so
# we don't want to use too many layers per data file.
DEFAULT_MAX_NUM_CHUNKS = 32


def write_parquet_batch(record_batch: RecordBatch) -> bytes:
    """Write a RecordBatch to a Parquet file

    We still use pyarrow.parquet.ParquetWriter if pyarrow is installed because pyarrow
    has better encoding defaults. So Parquet files written by pyarrow are smaller by
    default than files written by arro3.io.write_parquet.
    """
    # Occasionally it's possible for there to be empty batches in the
    # pyarrow table. This will error when writing to parquet. We want to
    # give a more informative error.
    if record_batch.num_rows == 0:
        raise ValueError("Batch with 0 rows.")

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        bio = BytesIO()
        with pq.ParquetWriter(
            bio,
            schema=pa.schema(record_batch.schema),
            compression=DEFAULT_PARQUET_COMPRESSION,
            compression_level=DEFAULT_PARQUET_COMPRESSION_LEVEL,
        ) as writer:
            writer.write_batch(
                pa.record_batch(record_batch), row_group_size=record_batch.num_rows
            )

        return bio.getvalue()

    except ImportError:
        from arro3.io import write_parquet

        compression_string = (
            f"{DEFAULT_PARQUET_COMPRESSION}({DEFAULT_PARQUET_COMPRESSION_LEVEL})"
        )
        bio = BytesIO()
        write_parquet(
            record_batch,
            bio,
            compression=compression_string,
            max_row_group_size=record_batch.num_rows,
        )

        return bio.getvalue()


def serialize_table_to_parquet(table: Table, *, max_chunksize: int) -> List[bytes]:
    buffers: List[bytes] = []
    assert max_chunksize > 0

    for record_batch in table.rechunk(max_chunksize=max_chunksize).to_batches():
        buffers.append(write_parquet_batch(record_batch))

    return buffers


def serialize_pyarrow_column(
    data: Array | ChunkedArray, *, max_chunksize: int
) -> List[bytes]:
    """Serialize a pyarrow column to a Parquet file with one column"""
    pyarrow_table = Table.from_pydict({"value": data})
    return serialize_table_to_parquet(pyarrow_table, max_chunksize=max_chunksize)


def serialize_accessor(data: Union[List[int], Tuple[int], NDArray[np.uint8]], obj):
    if data is None:
        return None

    # We assume data has already been validated to the right type for this accessor
    # Allow any json-serializable type through
    if isinstance(data, (str, int, float, list, tuple, bytes)):
        return data

    assert isinstance(data, (ChunkedArray, Array))
    validate_accessor_length_matches_table(data, obj.table)
    return serialize_pyarrow_column(data, max_chunksize=obj._rows_per_chunk)


def serialize_table(data, obj):
    assert isinstance(data, Table), "expected Arrow table"
    return serialize_table_to_parquet(data, max_chunksize=obj._rows_per_chunk)


def infer_rows_per_chunk(table: Table) -> int:
    # At least one chunk
    num_chunks = max(round(table.nbytes / DEFAULT_ARROW_CHUNK_BYTES_SIZE), 1)

    # Clamp to the maximum number of chunks
    num_chunks = min(num_chunks, DEFAULT_MAX_NUM_CHUNKS)

    rows_per_chunk = math.ceil((table.num_rows / num_chunks))
    return rows_per_chunk


def validate_accessor_length_matches_table(
    accessor: Array | ChunkedArray, table: Table
):
    if len(accessor) != len(table):
        raise TraitError("accessor must have same length as table")


def serialize_view_state(data: Optional[ViewState], obj):
    if data is None:
        return None

    return data._asdict()


ACCESSOR_SERIALIZATION = {"to_json": serialize_accessor}
TABLE_SERIALIZATION = {"to_json": serialize_table}

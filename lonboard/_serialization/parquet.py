from __future__ import annotations

import math
from io import BytesIO
from typing import TYPE_CHECKING, Any, overload

import arro3.compute as ac
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    RecordBatch,
    Scalar,
    Table,
    list_array,
    list_flatten,
    list_offsets,
)
from traitlets import TraitError

from lonboard._utils import timestamp_start_offset

if TYPE_CHECKING:
    from lonboard._layer import BaseArrowLayer
    from lonboard.experimental._layer import TripsLayer
    from lonboard.models import ViewState


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
    """Write a RecordBatch to a Parquet file.

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
                pa.record_batch(record_batch),
                row_group_size=record_batch.num_rows,
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


def serialize_table_to_parquet(table: Table, *, max_chunksize: int) -> list[bytes]:
    buffers: list[bytes] = []
    assert max_chunksize > 0

    for record_batch in table.rechunk(max_chunksize=max_chunksize).to_batches():
        buffers.append(write_parquet_batch(record_batch))

    return buffers


def serialize_pyarrow_column(
    data: Array | ChunkedArray,
    *,
    max_chunksize: int,
) -> list[bytes]:
    """Serialize a pyarrow column to a Parquet file with one column."""
    pyarrow_table = Table.from_pydict({"value": data})
    return serialize_table_to_parquet(pyarrow_table, max_chunksize=max_chunksize)


@overload
def serialize_accessor(
    data: ChunkedArray,
    obj: BaseArrowLayer,
) -> list[bytes]: ...
@overload
def serialize_accessor(
    data: str | float | list | tuple | bytes,
    obj: BaseArrowLayer,
) -> str | int | float | list | tuple | bytes: ...
def serialize_accessor(
    data: str | float | list | tuple | bytes | ChunkedArray,
    obj: BaseArrowLayer,
):
    if data is None:
        return None

    # We assume data has already been validated to the right type for this accessor
    # Allow any json-serializable type through
    if isinstance(data, (str, int, float, list, tuple, bytes)):
        return data

    assert isinstance(data, ChunkedArray)
    validate_accessor_length_matches_table(data, obj.table)
    return serialize_pyarrow_column(data, max_chunksize=obj._rows_per_chunk)  # noqa: SLF001


def serialize_table(data: Table, obj: BaseArrowLayer) -> list[bytes]:
    assert isinstance(data, Table), "expected Arrow table"
    return serialize_table_to_parquet(data, max_chunksize=obj._rows_per_chunk)  # noqa: SLF001


def infer_rows_per_chunk(table: Table) -> int:
    # At least one chunk
    num_chunks = max(round(table.nbytes / DEFAULT_ARROW_CHUNK_BYTES_SIZE), 1)

    # Clamp to the maximum number of chunks
    num_chunks = min(num_chunks, DEFAULT_MAX_NUM_CHUNKS)

    return math.ceil(table.num_rows / num_chunks)


def validate_accessor_length_matches_table(
    accessor: Array | ChunkedArray,
    table: Table,
) -> None:
    if len(accessor) != len(table):
        raise TraitError("accessor must have same length as table")


def serialize_view_state(data: ViewState | None, obj: Any) -> None | dict[str, Any]:  # noqa: ARG001
    if data is None:
        return None

    return data._asdict()


def serialize_timestamp_accessor(
    timestamps: ChunkedArray,
    obj: TripsLayer,
) -> list[bytes]:
    """Subtract off min timestamp to fit into f32 integer range.

    Then cast to float32.
    """
    # Note: this has some overlap with `timestamp_max_physical_value` in utils.
    # Cast to int64 type
    timestamps = timestamps.cast(DataType.list(DataType.int64()))

    start_offset_adjustment = Scalar(
        timestamp_start_offset(timestamps),
        type=DataType.int64(),
    )

    list_offsets_iter = list_offsets(timestamps)
    inner_values_iter = list_flatten(timestamps)

    offsetted_chunks = []
    for offsets, inner_values in zip(
        list_offsets_iter,
        inner_values_iter,
        strict=True,
    ):
        offsetted_values = ac.add(inner_values, start_offset_adjustment)
        f32_values = offsetted_values.cast(DataType.int64()).cast(DataType.float32())
        offsetted_chunks.append(list_array(offsets, f32_values))

    f32_timestamps_col = ChunkedArray(offsetted_chunks)
    return serialize_accessor(f32_timestamps_col, obj)


ACCESSOR_SERIALIZATION = {"to_json": serialize_accessor}
TIMESTAMP_ACCESSOR_SERIALIZATION = {"to_json": serialize_timestamp_accessor}
TABLE_SERIALIZATION = {"to_json": serialize_table}

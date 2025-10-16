from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from .base import ArrowSerialization
from .config import DEFAULT_PARQUET_COMPRESSION, DEFAULT_PARQUET_COMPRESSION_LEVEL

if TYPE_CHECKING:
    from arro3.core import RecordBatch


class Arro3ParquetSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Parquet using arro3."""

    def __init__(self) -> None:
        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
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


class Arro3IPCSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Arrow IPC using arro3."""

    def __init__(self) -> None:
        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
        """Write a single RecordBatch to an Arrow IPC stream in memory and return the bytes."""
        from arro3.io import write_ipc_stream

        bio = BytesIO()
        write_ipc_stream(record_batch, bio, compression=None)

        return bio.getvalue()

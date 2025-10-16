from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from .base import ArrowSerialization
from .config import DEFAULT_PARQUET_COMPRESSION, DEFAULT_PARQUET_COMPRESSION_LEVEL

if TYPE_CHECKING:
    from arro3.core import RecordBatch


class PyArrowParquetSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Parquet using pyarrow."""

    def __init__(self) -> None:
        # Validate that pyarrow is installed
        import pyarrow.parquet  # noqa: F401

        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
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


class PyArrowIPCSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Arrow IPC using pyarrow."""

    def __init__(self) -> None:
        # Validate that pyarrow is installed
        import pyarrow as pa  # noqa: F401

        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
        """Write a single RecordBatch to an Arrow IPC stream in memory and return the bytes."""
        import pyarrow as pa

        bio = BytesIO()
        with pa.ipc.new_stream(
            bio,
            schema=pa.schema(record_batch.schema),
            options=pa.ipc.IpcWriteOptions(compression=None),
        ) as writer:
            writer.write_batch(pa.record_batch(record_batch))

        return bio.getvalue()

from __future__ import annotations

from typing import TYPE_CHECKING

from lonboard._serialization.table.arro3 import (
    Arro3IPCSerialization,
    Arro3ParquetSerialization,
)
from lonboard._serialization.table.base import ArrowSerialization
from lonboard._serialization.table.pyarrow import (
    PyArrowIPCSerialization,
    PyArrowParquetSerialization,
)

if TYPE_CHECKING:
    from arro3.core import RecordBatch


class ParquetSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Parquet.

    Uses `pyarrow` if installed, otherwise falls back to `arro3.io`.
    """

    _impl: ArrowSerialization

    def __init__(self) -> None:
        try:
            import pyarrow.parquet
        except ImportError:
            self._impl = Arro3ParquetSerialization()
        else:
            self._impl = PyArrowParquetSerialization()

        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
        return self._impl._serialize_arrow_batch(record_batch)  # noqa SLF001


class IPCSerialization(ArrowSerialization):
    """Serialize Arrow Tables and Arrays to Arrow IPC.

    Uses `pyarrow` if installed, otherwise falls back to `arro3.io`.
    """

    _impl: ArrowSerialization

    def __init__(self) -> None:
        try:
            import pyarrow as pa
        except ImportError:
            self._impl = Arro3IPCSerialization()
        else:
            self._impl = PyArrowIPCSerialization()

        super().__init__()

    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
        return self._impl._serialize_arrow_batch(record_batch)  # noqa SLF001

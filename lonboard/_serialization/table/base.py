from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, overload

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
    from arro3.core import Array, RecordBatch

    from lonboard._layer import BaseArrowLayer
    from lonboard.experimental._layer import TripsLayer


class ArrowSerialization(ABC):
    """Base class for serializing Arrow Tables and Arrays.

    Ipywidgets does not easily support streaming of data, and the transport can choke on
    large single buffers. Therefore, we split a table into multiple RecordBatches and
    serialize them individually. Then we send a list of buffers to the frontend.
    """

    @abstractmethod
    def _serialize_arrow_batch(self, record_batch: RecordBatch) -> bytes:
        """Serialize one Arrow RecordBatch to a buffer."""

    def _serialize_arrow_table(
        self,
        table: Table,
        *,
        max_chunksize: int,
    ) -> list[bytes]:
        assert max_chunksize > 0

        batches = table.rechunk(max_chunksize=max_chunksize).to_batches()
        if any(batch.num_rows == 0 for batch in batches):
            raise ValueError("Batch with 0 rows.")

        with ThreadPoolExecutor() as executor:
            return list(executor.map(self._serialize_arrow_batch, batches))

    def _serialize_arrow_column(
        self,
        array: Array | ChunkedArray,
        *,
        max_chunksize: int,
    ) -> list[bytes]:
        """Serialize an Arrow Array or Column as a table with one column named "value"."""
        pyarrow_table = Table.from_pydict({"value": array})
        return self._serialize_arrow_table(pyarrow_table, max_chunksize=max_chunksize)

    def serialize_table(
        self,
        table: Table,
        obj: BaseArrowLayer,
    ) -> list[bytes]:
        """Serialize an Arrow Table from a widget."""
        assert isinstance(table, Table), "expected Arrow table"
        return self._serialize_arrow_table(table, max_chunksize=obj._rows_per_chunk)  # noqa: SLF001

    @overload
    def serialize_accessor(
        self,
        data: ChunkedArray,
        obj: BaseArrowLayer,
    ) -> list[bytes]: ...
    @overload
    def serialize_accessor(
        self,
        data: str | float | list | tuple | bytes,
        obj: BaseArrowLayer,
    ) -> str | int | float | list | tuple | bytes: ...
    def serialize_accessor(
        self,
        data: str | float | list | tuple | bytes | ChunkedArray,
        obj: BaseArrowLayer,
    ):
        """Serialize an Arrow Array or Column from a widget."""
        if data is None:
            return None

        # We assume data has already been validated to the right type for this accessor
        # Allow any json-serializable type through
        if isinstance(data, (str, int, float, list, tuple, bytes)):
            return data

        assert isinstance(data, ChunkedArray)
        validate_accessor_length_matches_table(data, obj.table)
        return self._serialize_arrow_column(data, max_chunksize=obj._rows_per_chunk)  # noqa: SLF001

    def serialize_timestamps(
        self,
        timestamps: ChunkedArray,
        obj: TripsLayer,
    ) -> list[bytes]:
        """Serialize timestamps for TripsLayer.

        Subtract off min timestamp to fit into f32 integer range. Then cast to float32.
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
            f32_values = offsetted_values.cast(DataType.int64()).cast(
                DataType.float32(),
            )
            offsetted_chunks.append(list_array(offsets, f32_values))

        f32_timestamps_col = ChunkedArray(offsetted_chunks)
        return self.serialize_accessor(f32_timestamps_col, obj)


def validate_accessor_length_matches_table(
    accessor: Array | ChunkedArray,
    table: Table,
) -> None:
    if len(accessor) != len(table):
        raise TraitError("accessor must have same length as table")

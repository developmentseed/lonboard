from __future__ import annotations

from typing import TYPE_CHECKING

from lonboard import config
from lonboard._serialization.table import (
    ArrowSerialization,
    IPCSerialization,
    ParquetSerialization,
)

if TYPE_CHECKING:
    from arro3.core import ChunkedArray, Table

    from lonboard._layer import BaseArrowLayer
    from lonboard.experimental._layer import TripsLayer


def _choose_serialization() -> ArrowSerialization:
    """Handle choice of serialization method.

    NOTE: we handle this choice **inside of `serialize_` functions** so that the choice
    can be changed at runtime. We don't want a specific serialization class to be
    attached to layer instances, because then it wouldn't update if the config changes.
    """
    if config.USE_PARQUET:
        return ParquetSerialization()

    return IPCSerialization()


def serialize_accessor(
    data: str | float | list | tuple | bytes | ChunkedArray,
    obj: BaseArrowLayer,
) -> str | int | float | list | tuple | bytes | list[bytes]:
    """Serialize an Arrow Array or Column from a widget."""
    return _choose_serialization().serialize_accessor(data, obj)


def serialize_timestamps(
    timestamps: ChunkedArray,
    obj: TripsLayer,
) -> list[bytes]:
    """Serialize timestamps for TripsLayer."""
    return _choose_serialization().serialize_timestamps(timestamps, obj)


def serialize_table(
    table: Table,
    obj: BaseArrowLayer,
) -> list[bytes]:
    """Serialize an Arrow Table from a widget."""
    return _choose_serialization().serialize_table(table, obj)


ACCESSOR_SERIALIZATION = {"to_json": serialize_accessor}
TIMESTAMP_SERIALIZATION = {"to_json": serialize_timestamps}
TABLE_SERIALIZATION = {"to_json": serialize_table}

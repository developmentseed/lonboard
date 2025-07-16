"""Import Arrow data from a C stream into a Table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from arro3.core import ArrayReader, ChunkedArray, DataType, Table

if TYPE_CHECKING:
    from arro3.core.types import ArrowStreamExportable


def import_arrow_c_stream(stream: ArrowStreamExportable) -> Table | ChunkedArray:
    """Import an Arrow stream into a Table.

    If the stream is a struct but **not** a geoarrow extension type, then we assume it's
    table input. Otherwise, we assume it's an array input, which we then coerce into a
    Table with a single field named "geometry".
    """
    array_reader = ArrayReader.from_arrow(stream)

    if DataType.is_struct(
        array_reader.field.type,
    ) and not array_reader.field.metadata_str.get(
        "ARROW:extension:name",
        "",
    ).startswith("geoarrow"):
        # If the field is a struct but **not** a geoarrow extension type, then we assume
        # it's table input.
        return Table.from_arrow(array_reader)

    return ChunkedArray.from_arrow(array_reader)

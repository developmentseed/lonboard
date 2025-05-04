# ruff: noqa

from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING, Any

import arro3.compute as ac
from arro3.core import (
    Array,
    ChunkedArray,
    DataType,
    Scalar,
    Table,
    list_array,
    list_flatten,
    list_offsets,
)

from lonboard._constants import MAX_INTEGER_FLOAT32, MIN_INTEGER_FLOAT32
from lonboard._serialization import TIMESTAMP_ACCESSOR_SERIALIZATION
from lonboard._utils import get_geometry_column_index
from lonboard.traits import FixedErrorTraitType

if TYPE_CHECKING:
    from traitlets.traitlets import TraitType

    from lonboard._layer import BaseArrowLayer


class TimestampAccessor(FixedErrorTraitType):
    """A representation of a deck.gl coordinate-timestamp accessor.

    deck.gl handles timestamps on the GPU as float32 values. This class will validate
    that the input timestamps are representable as float32 integers, and will
    automatically reduce the precision of input data if necessary to fit inside a
    float32.

    Accepted input includes:

    - A pyarrow [`ListArray`][pyarrow.ListArray] containing a temporal array such as a
        TimestampArray. Each value in the array will be used as the value for the object
        at the same row index.
    - Any Arrow list array containing a temporal array from a library that implements
      the [Arrow PyCapsule
      Interface](https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html).
    """

    default_value = None
    info_text = "a Arrow ListArray representing a nested array of timestamps"

    def __init__(
        self: TraitType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tag(sync=True, **TIMESTAMP_ACCESSOR_SERIALIZATION)

    def _reduce_precision(
        self,
        obj: BaseArrowLayer,
        value: ChunkedArray,
    ) -> ChunkedArray:
        # First, find the "spread" of existing values: the range between min and max of
        # the existing timestamps.
        min_val = ac.min(list_flatten(value))
        max_val = ac.max(list_flatten(value))

        # deck.gl stores timestamps as float32. Therefore, we need to validate that the
        # actual range of our data fits into the float32 integer range.
        actual_spread = ac.sub(max_val, min_val).cast(DataType.int64())[0].as_py()
        acceptable_spread = MAX_INTEGER_FLOAT32 - MIN_INTEGER_FLOAT32

        # If if already fits into the float32 integer range, we're done.
        if actual_spread <= acceptable_spread:
            return value

        # Otherwise, we need to reduce the precision of our data. We can do this by
        # changing the time unit of our data. So if our timestamps start with nanosecond
        # precision, we can downcast our data to microsecond, millisecond, or second
        # precision.
        # First, we want to figure out how many digits of precision to remove.
        digits_to_remove = math.log10(actual_spread / acceptable_spread)

        # Access the existing time unit and timezone
        value_type = value.type.value_type
        assert value_type is not None
        time_unit = value_type.time_unit
        tz = value_type.tz

        # We can only reduce precision in orders of 1,000.
        if digits_to_remove <= 3:
            digits_to_remove = 3
        elif digits_to_remove <= 6:
            digits_to_remove = 6
        elif digits_to_remove <= 9:
            digits_to_remove = 9
        else:
            # Cause the exception to be raised in the next block
            digits_to_remove = 999999

        # Validate that the precision reduction is possible. E.g. we can't reduce the
        # precision of second timestamps because we have no way to represent timestamps
        # larger than a second.
        if (
            (time_unit == "ns" and digits_to_remove > 9)
            or (time_unit == "us" and digits_to_remove > 6)
            or (time_unit == "ms" and digits_to_remove > 3)
            or (time_unit == "s")
        ):
            self.error(
                obj,
                value,
                info=(
                    "The range of the timestamp column cannot is larger than what "
                    "can be represented at second precision in a float32. deck.gl "
                    "uses float32 for the timestamps in the TripsLayer. "
                    "Choose a smaller temporal subset of data."
                ),
            )

        # Figure out the new data type given the existing data type and the number of
        # digits of precision we're removing.
        if time_unit == "ns":
            if digits_to_remove == 3:
                new_data_type = DataType.timestamp("us", tz=tz)
            elif digits_to_remove == 6:
                new_data_type = DataType.timestamp("ms", tz=tz)
            elif digits_to_remove == 9:
                new_data_type = DataType.timestamp("s", tz=tz)
            else:
                assert False
        elif time_unit == "us":
            if digits_to_remove == 3:
                new_data_type = DataType.timestamp("ms", tz=tz)
            elif digits_to_remove == 6:
                new_data_type = DataType.timestamp("s", tz=tz)
            else:
                assert False
        elif time_unit == "ms":
            if digits_to_remove == 3:
                new_data_type = DataType.timestamp("s", tz=tz)
            else:
                assert False
        else:
            assert False

        new_time_unit = new_data_type.time_unit
        warnings.warn(
            f"Reducing precision of input timestamp data to '{new_time_unit}'"
            " to fit into available GPU precision.",
        )

        # Actually reduce the precision of each chunk of the input data, assigning the
        # new data type
        offsets_reader = list_offsets(value)
        inner_values_reader = list_flatten(value)

        divisor = Scalar(int(math.pow(10, digits_to_remove)), type=DataType.int64())

        reduced_precision_chunks = []
        for offsets, inner_values in zip(offsets_reader, inner_values_reader):
            reduced_precision_values = ac.div(
                inner_values.cast(DataType.int64()),
                divisor,
            )
            reduced_precision_chunks.append(
                list_array(offsets, reduced_precision_values.cast(new_data_type)),
            )

        return ChunkedArray(reduced_precision_chunks)

    def _validate_timestamp_offsets(self, obj: BaseArrowLayer, value: ChunkedArray):
        """Validate that the offsets of the list array used for the timestamp column match
        the offsets of the list array used for the LineString array in the geometry
        column.
        """
        table: Table = obj.table
        geom_idx = get_geometry_column_index(table.schema)
        assert geom_idx is not None
        geom_col = table.column(geom_idx)

        # TODO: this chunking may not match depending on whether the table has already
        # been rechunked by this point.
        for geom_chunk, timestamp_chunk in zip(geom_col.chunks, value.chunks):
            geom_offsets = list_offsets(geom_chunk)
            timestamp_offsets = list_offsets(timestamp_chunk)
            if geom_offsets != timestamp_offsets:
                self.error(
                    obj,
                    value,
                    info="timestamp array's offsets to match geometry array's offsets.",
                )

    def validate(self, obj: BaseArrowLayer, value) -> ChunkedArray:
        if hasattr(value, "__arrow_c_array__"):
            value = ChunkedArray([Array.from_arrow(value)])
        elif hasattr(value, "__arrow_c_stream__"):
            value = ChunkedArray.from_arrow(value)
        else:
            self.error(obj, value)

        assert isinstance(value, ChunkedArray)

        if not DataType.is_list(value.type):
            self.error(obj, value, info="timestamp array to be a list-type array")

        value_type = value.type.value_type
        assert value_type is not None
        if not DataType.is_temporal(value_type):
            self.error(obj, value, info="timestamp array to have a temporal child.")

        value = self._reduce_precision(obj, value)
        value = value.rechunk(max_chunksize=obj._rows_per_chunk)
        self._validate_timestamp_offsets(obj, value)
        return value

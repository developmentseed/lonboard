from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pytest
from arro3.core import Table
from geoarrow.rust.core import linestrings

from lonboard import TripsLayer
from lonboard._constants import MIN_INTEGER_FLOAT32

# The first timestamp of the test data, 2023-07-01T16:00:00Z.
START = datetime(2023, 7, 1, 16)  # noqa: DTZ001
START_SECONDS = 1_688_227_200

UNITS_PER_SECOND = {"s": 1, "ms": 10**3, "us": 10**6, "ns": 10**9}

# The smallest step in each time unit that a `datetime` can represent.
STEP = {
    "s": timedelta(seconds=1),
    "ms": timedelta(milliseconds=1),
    "us": timedelta(microseconds=1),
    "ns": timedelta(microseconds=1),
}


def trips_layer(time_unit: str, tz: str | None = None, **kwargs: Any) -> TripsLayer:
    """Create a layer with two trips that together span 9,000 time units."""
    coords = np.array([[0, 0], [1, 1], [2, 2], [3, 3]], dtype=np.float64)
    offsets = np.array([0, 2, 4], dtype=np.int32)
    geometry = linestrings(coords, offsets, crs="EPSG:4326")
    table = Table.from_arrays([geometry], names=["geometry"])

    start = START_SECONDS * UNITS_PER_SECOND[time_unit]
    timestamps = pa.array(
        [[start, start + 3_000], [start + 6_000, start + 9_000]],
        type=pa.list_(pa.int64()),
    ).cast(pa.list_(pa.timestamp(time_unit, tz=tz)))

    return TripsLayer(table, get_timestamps=timestamps, **kwargs)


def test_current_time_kwarg():
    current_time = START + timedelta(seconds=30)
    layer = trips_layer("s", current_time=current_time)
    assert layer.current_time == current_time


@pytest.mark.parametrize("time_unit", ["s", "ms", "us", "ns"])
def test_current_time_round_trip(time_unit):
    layer = trips_layer(time_unit)

    for i in range(10):
        current_time = START + i * STEP[time_unit]
        layer.current_time = current_time
        assert layer.current_time == current_time


@pytest.mark.parametrize("time_unit", ["s", "ms", "us", "ns"])
def test_current_time_setter_start_of_data(time_unit):
    layer = trips_layer(time_unit)
    layer.current_time = START

    # The timestamps sent to the frontend start at the smallest float32 integer
    assert layer._current_time == MIN_INTEGER_FLOAT32


@pytest.mark.parametrize("tz", [None, "UTC", "America/New_York", "+02:00"])
def test_current_time_setter_accepts_getter_value(tz):
    layer = trips_layer("s", tz=tz)
    layer._current_time = MIN_INTEGER_FLOAT32 + 30

    layer.current_time = layer.current_time
    assert layer._current_time == MIN_INTEGER_FLOAT32 + 30


def test_current_time_round_trip_timezone():
    layer = trips_layer("s", tz="America/New_York")

    # New York is on daylight saving time in July, but not at the Unix epoch
    current_time = datetime(2023, 7, 1, 12, 0, 30, tzinfo=ZoneInfo("America/New_York"))
    layer.current_time = current_time
    assert layer.current_time == current_time


def test_current_time_setter_other_timezone():
    layer = trips_layer("s", tz="America/New_York")
    layer.current_time = datetime(2023, 7, 1, 16, 0, 30, tzinfo=UTC)

    assert layer._current_time == MIN_INTEGER_FLOAT32 + 30


def test_current_time_setter_naive_datetime_for_timestamps_with_timezone():
    layer = trips_layer("s", tz="America/New_York")

    with pytest.raises(TypeError, match="timezone"):
        layer.current_time = datetime(2023, 7, 1, 12, 0, 30)  # noqa: DTZ001


def test_current_time_setter_aware_datetime_for_timestamps_without_timezone():
    layer = trips_layer("s")

    with pytest.raises(TypeError, match="timezone"):
        layer.current_time = datetime(2023, 7, 1, 16, 0, 30, tzinfo=UTC)


@pytest.mark.parametrize(
    "value",
    [START_SECONDS, "2023-07-01T16:00:00", date(2023, 7, 1)],
)
def test_current_time_setter_type_error(value):
    layer = trips_layer("s")

    with pytest.raises(TypeError, match="to be a datetime, got"):
        layer.current_time = value


def test_current_time_setter_drops_precision_finer_than_time_unit():
    layer = trips_layer("s")
    layer.current_time = START + timedelta(seconds=30, microseconds=999_999)

    assert layer.current_time == START + timedelta(seconds=30)


def test_current_time_setter_outside_data_range():
    layer = trips_layer("s")

    current_time = START - timedelta(days=1)
    layer.current_time = current_time
    assert layer.current_time == current_time

import sys
from concurrent.futures import Future, ThreadPoolExecutor

import pytest

from lonboard._executor import Executor, MainThreadExecutor


def test_submit_returns_future_with_result():
    with MainThreadExecutor() as executor:
        future = executor.submit(lambda x: x + 1, 41)

    assert isinstance(future, Future)
    assert future.result() == 42


def test_submit_captures_exception():
    def raises():
        raise ValueError("boom")

    with MainThreadExecutor() as executor:
        future = executor.submit(raises)

    with pytest.raises(ValueError, match="boom"):
        future.result()


def test_map_preserves_order():
    with MainThreadExecutor() as executor:
        results = list(executor.map(lambda x: x * 2, [1, 2, 3]))

    assert results == [2, 4, 6]


def test_accepts_max_workers():
    with MainThreadExecutor(max_workers=4) as executor:
        future = executor.submit(lambda: 1)

    assert future.result() == 1


def test_executor_is_threadpool_outside_emscripten():
    assert sys.platform != "emscripten"
    assert Executor is ThreadPoolExecutor

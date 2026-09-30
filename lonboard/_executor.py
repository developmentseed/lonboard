"""Executor used for parallelizing work across chunks of an Arrow column.

On emscripten (Pyodide/JupyterLite), spawning threads is not supported, so
``Executor`` transparently swaps to an executor that runs tasks
synchronously on the calling thread.
"""

from __future__ import annotations

import sys
from concurrent.futures import Executor as _Executor
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


class MainThreadExecutor(_Executor):
    """An Executor that runs tasks immediately on the calling thread."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Accept and ignore ThreadPoolExecutor's ``max_workers`` argument."""

    def submit(  # type: ignore[override]
        self,
        fn: Callable[..., T],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Future[T]:
        future: Future[T] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001
            future.set_exception(exc)
        return future


Executor: type[MainThreadExecutor | ThreadPoolExecutor]
if sys.platform == "emscripten":
    Executor = MainThreadExecutor
else:
    Executor = ThreadPoolExecutor

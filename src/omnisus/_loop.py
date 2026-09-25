"""Run a coroutine from synchronous code, also inside a notebook's running event loop."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def run_sync[T](coroutine: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """Run ``coroutine()`` to completion, also from inside a running event loop.

    A marimo or Jupyter cell already runs in an event loop, where
    ``asyncio.run`` refuses to start another; there the coroutine gets its own
    loop on a worker thread and the caller blocks until it finishes. Every
    synchronous public function that awaits goes through here.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine())
    with ThreadPoolExecutor(max_workers=1) as worker:
        return worker.submit(lambda: asyncio.run(coroutine())).result()

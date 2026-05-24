"""Hard timeouts for DB work — avoids hung requests when Supabase pooler stalls."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_DB_TIMEOUT_SEC = 12.0


def run_db(
    fn: Callable[[], T],
    *,
    timeout_sec: float = DEFAULT_DB_TIMEOUT_SEC,
    label: str = "db",
) -> T:
    """
    Run a DB-only callable in a worker thread with a wall-clock timeout.

    On timeout we do NOT wait for the stuck thread (psycopg2 connect can hang
    indefinitely). Otherwise ``ThreadPoolExecutor`` shutdown would block the request.
    """
    pool = concurrent.futures.ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix=f"db-timeout-{label}",
    )
    timed_out = False
    fut = pool.submit(fn)
    try:
        return fut.result(timeout=timeout_sec)
    except concurrent.futures.TimeoutError as exc:
        timed_out = True
        logger.error("DB operation timed out after %.0fs (%s)", timeout_sec, label)
        raise TimeoutError(f"Database timed out ({label})") from exc
    finally:
        pool.shutdown(wait=not timed_out, cancel_futures=timed_out)

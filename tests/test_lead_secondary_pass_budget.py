"""Per-lead wall-clock budget for the secondary pass.

The secondary pass runs several sequential network calls per lead. Without a
hard ceiling, a single slow lead stalls the whole batch (the bug that hung the
run with zero DB writes). These tests pin the SIGALRM-based budget.
"""
from __future__ import annotations

import threading
import time

import pytest

from app.services.lead_secondary_pass import (
    LeadBudgetExceeded,
    _lead_budget_seconds,
    _lead_time_budget,
)


def test_lead_budget_seconds_default_and_env(monkeypatch):
    monkeypatch.delenv("SECONDARY_LEAD_BUDGET_SEC", raising=False)
    assert _lead_budget_seconds() == 45
    monkeypatch.setenv("SECONDARY_LEAD_BUDGET_SEC", "10")
    assert _lead_budget_seconds() == 10
    # Garbage falls back to the default rather than crashing the batch.
    monkeypatch.setenv("SECONDARY_LEAD_BUDGET_SEC", "not-a-number")
    assert _lead_budget_seconds() == 45


def test_budget_interrupts_a_slow_lead_on_main_thread():
    # A lead that blocks longer than its budget must be interrupted so the
    # batch can move on to the next candidate.
    started = time.monotonic()
    with pytest.raises(LeadBudgetExceeded):
        with _lead_time_budget(1):
            time.sleep(5)
    assert time.monotonic() - started < 3  # interrupted well before the 5s sleep


def test_budget_allows_fast_leads():
    with _lead_time_budget(2):
        time.sleep(0.05)  # under budget → no exception


def test_budget_zero_disables():
    # 0 = disabled: no timer armed, no interruption.
    with _lead_time_budget(0):
        time.sleep(0.05)


def test_budget_noop_off_main_thread():
    # SIGALRM is main-thread only; in a worker thread the budget must be a
    # no-op (we rely on per-request HTTP timeouts there) and never raise.
    errors: list[str] = []

    def worker():
        try:
            with _lead_time_budget(1):
                time.sleep(2)  # would trip the budget on main thread
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(repr(exc))

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=10)
    assert not errors

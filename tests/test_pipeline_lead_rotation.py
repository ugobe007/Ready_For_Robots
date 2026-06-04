"""Sales lead rotation window for 30-minute cache rebuilds."""

from app.api.leads import _rotate_staged_leads


def _staged(n: int) -> list[tuple]:
    return [(i, False, "", None) for i in range(n)]


def test_rotate_returns_all_when_pool_smaller_than_limit():
    staged = _staged(5)
    assert len(_rotate_staged_leads(staged, 30, slot=0)) == 5


def test_rotate_changes_window_by_slot():
    staged = _staged(100)
    a = _rotate_staged_leads(staged, 30, slot=0)
    b = _rotate_staged_leads(staged, 30, slot=1)
    assert len(a) == len(b) == 30
    assert a != b

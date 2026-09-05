"""Safe auto-send guards: daily cap parsing + angle-rotation fallback."""
from app.services import cal_autonomy as ca
from app.services.agent_messaging import BUYER_VARIANTS, pick_buyer_variant


def test_daily_send_cap_defaults_low(monkeypatch):
    monkeypatch.delenv("CAL_AUTONOMY_DAILY_CAP", raising=False)
    assert ca.cal_daily_send_cap() == 10


def test_daily_send_cap_env_override(monkeypatch):
    monkeypatch.setenv("CAL_AUTONOMY_DAILY_CAP", "3")
    assert ca.cal_daily_send_cap() == 3
    monkeypatch.setenv("CAL_AUTONOMY_DAILY_CAP", "garbage")
    assert ca.cal_daily_send_cap() == 10


def test_daily_sent_count_safe_without_redis(monkeypatch):
    # No Redis configured -> counters degrade to 0, never raise.
    monkeypatch.setattr(ca, "_redis_client", lambda: None)
    assert ca.cal_daily_sent_count() == 0
    ca._incr_daily_sent(5)  # must be a no-op, not an error


def test_active_buyer_variants_falls_back_to_all_on_error(monkeypatch):
    # No Redis + a db object that raises -> return every angle (never empty).
    monkeypatch.setattr(ca, "_redis_client", lambda: None)

    class _BoomDB:
        def query(self, *a, **k):
            raise RuntimeError("db down")

    result = ca.active_buyer_variants(_BoomDB())
    assert set(result) == set(BUYER_VARIANTS)


def test_pick_variant_respects_allowed_subset():
    only = (BUYER_VARIANTS[0], BUYER_VARIANTS[2])
    for cid in range(10):
        assert pick_buyer_variant(cid, allowed=only) in only

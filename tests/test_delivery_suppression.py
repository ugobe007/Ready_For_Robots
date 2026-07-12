"""Bounce-reason capture + address suppression for Cal outreach."""
from app.api.webhooks import _delivery_payload, _extract_problem_detail
from app.services.lead_enrichment import address_previously_bounced, recent_bounce_rate


def test_extract_problem_detail_reads_nested_bounce_object():
    data = {
        "email_id": "abc",
        "bounce": {
            "message": "The recipient's mailbox does not exist.",
            "type": "Permanent",
            "subType": "NoEmail",
        },
    }
    detail = _extract_problem_detail(data)
    assert detail["reason"] == "The recipient's mailbox does not exist."
    assert detail["type"] == "Permanent"
    assert detail["subtype"] == "NoEmail"


def test_extract_problem_detail_falls_back_to_flat_payload():
    detail = _extract_problem_detail({"reason": "flat reason"})
    assert detail["reason"] == "flat reason"


def test_delivery_payload_captures_hard_bounce_reason_and_class():
    data = {"bounce": {"message": "mailbox unavailable", "type": "Permanent"}}
    out = _delivery_payload(None, "email.bounced", data)
    # Reason is no longer the old empty/"unknown" — it comes from data['bounce'].
    assert out["problem_reason"] == "mailbox unavailable"
    assert out["problem_type"] == "Permanent"
    assert out["problem_class"] == "hard"
    assert out["delivery_events"][-1]["reason"] == "mailbox unavailable"


def test_delivery_payload_classifies_soft_bounce():
    data = {"bounce": {"message": "mailbox full", "type": "Transient"}}
    out = _delivery_payload(None, "email.bounced", data)
    assert out["problem_class"] == "soft"


def test_delivery_payload_complaint_is_hard():
    out = _delivery_payload(None, "email.complained", {"complaint": {"message": "spam"}})
    assert out["problem_class"] == "hard"
    assert out["problem_reason"] == "spam"


class _Query:
    def __init__(self, result, group_rows=None):
        self._result = result
        self._group_rows = group_rows or []

    def filter(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._group_rows

    def first(self):
        return self._result


class _FakeDB:
    def __init__(self, result=None, group_rows=None):
        self._result = result
        self._group_rows = group_rows

    def query(self, *args, **kwargs):
        return _Query(self._result, self._group_rows)


def test_address_previously_bounced_true_when_prior_bounce_row_exists():
    assert address_previously_bounced(_FakeDB(("row-id",)), "dead@acme.com") is True


def test_address_previously_bounced_false_when_no_row():
    assert address_previously_bounced(_FakeDB(None), "fresh@acme.com") is False


def test_address_previously_bounced_false_for_empty_email():
    # Short-circuits before touching the DB.
    assert address_previously_bounced(_FakeDB(("row-id",)), "") is False


# ── Deliverability circuit breaker ────────────────────────────────────────────

def test_recent_bounce_rate_computes_rate_and_folds_complaints():
    # 10 delivered, 8 bounced, 2 complained → 10 bad of 20 sent = 50%.
    rows = [("delivered", 10), ("bounced", 8), ("complained", 2)]
    stats = recent_bounce_rate(_FakeDB(group_rows=rows), hours=168)
    assert stats["sent"] == 20
    assert stats["delivered"] == 10
    assert stats["bounced"] == 10
    assert stats["rate"] == 0.5


def test_recent_bounce_rate_zero_sends_is_safe():
    stats = recent_bounce_rate(_FakeDB(group_rows=[]), hours=168)
    assert stats["sent"] == 0
    assert stats["rate"] == 0.0


def test_circuit_breaker_trips_above_threshold_with_sample():
    stats = recent_bounce_rate(
        _FakeDB(group_rows=[("delivered", 40), ("bounced", 20)]), hours=168
    )
    min_sample, threshold = 20, 0.10
    paused = stats["sent"] >= min_sample and stats["rate"] > threshold
    assert paused is True


def test_circuit_breaker_holds_below_min_sample():
    # Rate is awful (100%) but only 3 sends — too small to act on.
    stats = recent_bounce_rate(_FakeDB(group_rows=[("bounced", 3)]), hours=168)
    min_sample, threshold = 20, 0.10
    paused = stats["sent"] >= min_sample and stats["rate"] > threshold
    assert paused is False

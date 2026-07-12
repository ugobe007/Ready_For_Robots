"""Bounce-reason capture + address suppression for Cal outreach."""
from app.api.webhooks import _delivery_payload, _extract_problem_detail
from app.services.lead_enrichment import address_previously_bounced


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
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeDB:
    def __init__(self, result):
        self._result = result

    def query(self, *args, **kwargs):
        return _Query(self._result)


def test_address_previously_bounced_true_when_prior_bounce_row_exists():
    assert address_previously_bounced(_FakeDB(("row-id",)), "dead@acme.com") is True


def test_address_previously_bounced_false_when_no_row():
    assert address_previously_bounced(_FakeDB(None), "fresh@acme.com") is False


def test_address_previously_bounced_false_for_empty_email():
    # Short-circuits before touching the DB.
    assert address_previously_bounced(_FakeDB(("row-id",)), "") is False

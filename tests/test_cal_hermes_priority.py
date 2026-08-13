"""Cal prioritizes Hermes-qualified companies in the outreach pool."""
from types import SimpleNamespace

from app.services.cal_autonomy import (
    prioritize_hermes_qualified,
    prioritize_buying_window,
    _hermes_context_reason,
)


def test_prioritize_hermes_qualified_orders_by_fit():
    a = SimpleNamespace(id=1, crm_metadata={"hermes_qualify": {"automation_fit": 80}})
    b = SimpleNamespace(id=2, crm_metadata={})
    c = SimpleNamespace(id=3, crm_metadata={"hermes_qualify": {"automation_fit": 40}})
    companies = [(b, 90.0, "HOT"), (c, 88.0, "HOT"), (a, 70.0, "WARM")]
    out = prioritize_hermes_qualified(companies, min_fit=60.0)
    assert out[0][0].id == 1
    assert {x[0].id for x in out[1:]} == {2, 3}


def test_prioritize_buying_window_orders_by_urgency():
    a = SimpleNamespace(id=1, crm_metadata={"hermes_buying_window": {"urgency_0_100": 80}})
    b = SimpleNamespace(id=2, crm_metadata={})
    c = SimpleNamespace(id=3, crm_metadata={"hermes_buying_window": {"urgency_0_100": 40}})
    companies = [(b, 90.0, "HOT"), (c, 88.0, "HOT"), (a, 70.0, "WARM")]
    out = prioritize_buying_window(companies, min_urgency=50.0)
    assert out[0][0].id == 1
    assert {x[0].id for x in out[1:]} == {2, 3}


def test_hermes_context_reason_from_job_title():
    company = SimpleNamespace(
        name="GXO Logistics",
        crm_metadata={
            "hermes_qualify": {"automation_fit": 72},
            "hermes_job_orders": [{"job_title": "AMR Operator"}],
        },
    )
    reason = _hermes_context_reason(company)
    assert reason is not None
    assert "AMR Operator" in reason
    assert "caught my eye" in reason or "hiring" in reason


def test_hermes_context_reason_buying_window_when_flagged(monkeypatch):
    monkeypatch.setenv("CAL_INCLUDE_BUYING_WINDOW", "1")
    company = SimpleNamespace(
        name="Medline",
        crm_metadata={
            "hermes_qualify": {"automation_fit": 65},
            "hermes_buying_window": {
                "urgency_0_100": 70,
                "cal_hint": "Reference peer warehouse robotics expansion before Automate.",
            },
        },
    )
    reason = _hermes_context_reason(company)
    assert reason is not None
    assert "peer warehouse" in reason.lower() or "automate" in reason.lower()


def test_hermes_context_reason_ignores_buying_window_by_default(monkeypatch):
    monkeypatch.delenv("CAL_INCLUDE_BUYING_WINDOW", raising=False)
    company = SimpleNamespace(
        name="Medline",
        crm_metadata={
            "hermes_qualify": {"automation_fit": 65},
            "hermes_buying_window": {
                "urgency_0_100": 90,
                "cal_hint": "Reference peer warehouse robotics expansion before Automate.",
            },
        },
    )
    assert _hermes_context_reason(company) is None

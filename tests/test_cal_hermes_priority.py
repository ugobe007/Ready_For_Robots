"""Cal prioritizes Hermes-qualified companies in the outreach pool."""
from types import SimpleNamespace

from app.services.cal_autonomy import prioritize_hermes_qualified, _hermes_context_reason


def test_prioritize_hermes_qualified_orders_by_fit():
    a = SimpleNamespace(id=1, crm_metadata={"hermes_qualify": {"automation_fit": 80}})
    b = SimpleNamespace(id=2, crm_metadata={})
    c = SimpleNamespace(id=3, crm_metadata={"hermes_qualify": {"automation_fit": 40}})
    companies = [(b, 90.0, "HOT"), (c, 88.0, "HOT"), (a, 70.0, "WARM")]
    out = prioritize_hermes_qualified(companies, min_fit=60.0)
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

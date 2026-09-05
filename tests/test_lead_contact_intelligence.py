from types import SimpleNamespace
from unittest.mock import patch

from app.services.lead_contact_intelligence import enrich_company_contact_intelligence


def _signal(signal_text: str, signal_type: str = "automation_intent", source_url: str | None = None):
    return SimpleNamespace(signal_text=signal_text, signal_type=signal_type, source_url=source_url)


def test_contact_intelligence_extracts_phone_from_signal_text():
    company = SimpleNamespace(
        name="Acme Manufacturing",
        website=None,
        industry="Manufacturing",
        crm_metadata={
            "decision_makers": [{"name": "Jane Doe", "title": "VP Operations"}],
            "lead_inference": {
                "specific_problem": "Line throughput bottleneck",
                "why_lead": ["Capex approved", "Pilot underway"],
                "procurement": {"has_rfp": True},
                "timetable": {"window": "Q4 2026"},
                "application_areas": ["material handling"],
            },
        },
    )
    signals = [
        _signal("Call our automation team at +1 (415) 555-1212 for pilot rollout details.")
    ]

    with patch("app.services.lead_contact_intelligence._google_search_results", return_value=[]):
        payload = enrich_company_contact_intelligence(company, signals)

    assert payload["phone"]["best"]["phone"] == "+14155551212"
    assert payload["linkedin"]["status"] in {"not_found", "no_people", "needs_disambiguation", "ready"}
    assert payload["sales_intuition"]["why_sales_lead"]["specific_problem"] == "Line throughput bottleneck"


def test_contact_intelligence_flags_linkedin_disambiguation_when_scores_close():
    company = SimpleNamespace(
        name="Acme Manufacturing",
        website=None,
        industry="Manufacturing",
        crm_metadata={
            "decision_makers": [{"name": "Jane Doe", "title": "VP Operations"}],
            "lead_inference": {"why_lead": ["Deployment signal"]},
        },
    )
    signals = [_signal("Automation program announced.")]

    google_rows = [
        {
            "url": "https://www.linkedin.com/in/jane-doe-operations",
            "title": "Jane Doe - VP Operations - Acme Manufacturing",
            "snippet": "Current: VP Operations at Acme Manufacturing",
        },
        {
            "url": "https://www.linkedin.com/in/jane-doe-supply-chain",
            "title": "Jane Doe - Supply Chain Leader - Acme Manufacturing",
            "snippet": "Current: Supply Chain leader at Acme Manufacturing",
        },
    ]

    with patch("app.services.lead_contact_intelligence._google_search_results", return_value=google_rows):
        payload = enrich_company_contact_intelligence(company, signals)

    assert payload["linkedin"]["best_profile"] is not None
    assert payload["linkedin"]["status"] == "needs_disambiguation"
    assert payload["linkedin"]["disambiguation"] is not None
    assert payload["linkedin"]["disambiguation"]["target_person"] == "Jane Doe"


def test_contact_intelligence_uses_tel_link_from_website():
    company = SimpleNamespace(
        name="Beta Robotics Buyer",
        website="https://example.com",
        industry="Logistics",
        crm_metadata={
            "decision_makers": [{"name": "John Smith", "title": "Director Automation"}],
            "lead_inference": {"why_lead": ["Warehouse expansion"]},
        },
    )
    signals = [_signal("Warehouse robotics expansion planned.")]

    html = "<html><body><a href='tel:+1-206-555-3000'>Call sales</a></body></html>"

    with patch("app.services.lead_contact_intelligence._google_search_results", return_value=[]):
        with patch("app.services.lead_contact_intelligence._fetch_html", return_value=html):
            payload = enrich_company_contact_intelligence(company, signals)

    assert payload["phone"]["best"]["phone"] == "+12065553000"
    assert payload["phone"]["best"]["score"] >= 0.9

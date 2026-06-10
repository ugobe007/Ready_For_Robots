"""Unit tests for lead gap audit (secondary pass candidate selection)."""

from types import SimpleNamespace

from app.services.lead_gap_audit import audit_company_gaps, stamp_ledger_entry


def _company(**kwargs):
    defaults = {
        "id": 1,
        "name": "Acme Logistics",
        "website": None,
        "industry": "Unknown",
        "crm_metadata": {},
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_audit_detects_website_and_industry_gaps():
    # No http website or evidence URL → website gap
    signals = [SimpleNamespace(source_url="seed_v3", signal_text="Acme expands DC")]
    report = audit_company_gaps(_company(), signals, [], overall_score=62.0)
    assert "website" in report.gaps
    assert "industry" in report.gaps
    assert report.passes


def test_audit_skips_website_when_present():
    signals = [SimpleNamespace(source_url="https://news.example/a", signal_text="Acme expands")]
    report = audit_company_gaps(
        _company(website="https://acme.example", industry="Logistics"),
        signals,
        [SimpleNamespace(email="ops@acme.example", title="VP Ops")],
        overall_score=80.0,
    )
    assert "website" not in report.gaps
    assert "industry" not in report.gaps


def test_audit_skips_contact_when_outreach_email_in_metadata():
    signals = [SimpleNamespace(source_url="seed_v3", signal_text="Acme expands")]
    report = audit_company_gaps(
        _company(crm_metadata={"outreach_email": "operations@acme.example"}),
        signals,
        [],
        overall_score=70.0,
    )
    assert "contact" not in report.gaps


def test_stamp_ledger_entry_persists_on_crm_metadata():
    company = _company(crm_metadata={"lead_inference": {"specific_problem": "Labor gap"}})
    stamp_ledger_entry(company, "website_rescue", status="filled", fields_filled=["website"])
    ledger = company.crm_metadata.get("enrichment_ledger", {})
    assert ledger["website_rescue"]["status"] == "filled"
    assert ledger["website_rescue"]["fields_filled"] == ["website"]

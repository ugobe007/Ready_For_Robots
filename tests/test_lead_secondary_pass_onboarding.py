"""Secondary pass onboarding for newly scraped leads."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.lead_secondary_pass import (
    ONBOARDING_PASSES,
    PASS_AGENT_QA,
    PASS_INDUSTRY,
    _merge_onboarding_passes,
    run_secondary_pass_for_company_ids,
)
from app.services.lead_gap_audit import LeadGapReport, PASS_RECTIFY


def test_merge_onboarding_passes_adds_full_sweep():
    report = LeadGapReport(
        company_id=1,
        company_name="Acme",
        gaps=["industry"],
        passes=[PASS_INDUSTRY],
    )
    merged = _merge_onboarding_passes(report, onboarding=True)
    assert PASS_RECTIFY in merged.passes
    assert PASS_AGENT_QA in merged.passes
    assert merged.passes[0] == PASS_INDUSTRY


def test_run_secondary_pass_for_company_ids_empty():
    db = MagicMock()
    out = run_secondary_pass_for_company_ids(db, [], rescore=False)
    assert out["processed"] == 0
    assert out["candidates"] == 0


def test_onboarding_pass_list_covers_pillars():
    assert PASS_RECTIFY in ONBOARDING_PASSES
    assert PASS_INDUSTRY in ONBOARDING_PASSES
    assert PASS_AGENT_QA in ONBOARDING_PASSES

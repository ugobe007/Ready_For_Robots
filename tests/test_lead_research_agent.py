"""Lead research agent selection, dedupe, and dry-run behavior."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register metadata
from app.database import Base
from app.models.company import Company
from app.models.lead_research import LeadResearchUpdate
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_research_agent import (
    NormalizedResearchResult,
    dedupe_fingerprint,
    ensure_signal_for_research_result,
    materiality_score,
    normalize_research_results,
    research_company_updates,
    rescore_company,
    select_research_candidates,
    signal_type_for_update,
    update_crm_profile_from_research,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _qualified_company(db_session, name: str = "Acme Logistics LLC") -> Company:
    company = Company(name=name, industry="Logistics", source="test")
    db_session.add(company)
    db_session.flush()
    db_session.add(
        Score(
            company_id=company.id,
            automation_score=78,
            labor_pain_score=80,
            expansion_score=84,
            robotics_fit_score=76,
            overall_intent_score=88,
        )
    )
    db_session.add(
        Signal(
            company_id=company.id,
            signal_type="expansion",
            signal_text=f"{name} is opening a new distribution center and needs warehouse automation capacity.",
            signal_strength=0.9,
            source_url="https://example.com/acme-expansion",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    db_session.refresh(company)
    return company


def test_select_research_candidates_prefers_qualified_hot_or_warm_leads(db_session):
    good = _qualified_company(db_session)
    bad = Company(name="Robotics Market Outlook", industry="Research", source="test")
    db_session.add(bad)
    db_session.commit()

    candidates = select_research_candidates(db_session, limit=10)

    assert [c.id for c in candidates] == [good.id]


def test_normalize_research_results_scores_material_update(db_session):
    company = _qualified_company(db_session)

    updates = normalize_research_results(company, lookback_days=30, max_results=2)

    assert len(updates) == 1
    assert updates[0].update_type == "expansion"
    assert updates[0].source_domain == "example.com"
    assert updates[0].significance_score >= 0.9


def test_research_company_updates_dry_run_does_not_write(db_session):
    company = _qualified_company(db_session)

    summary = research_company_updates(db_session, company.id, dry_run=True)

    assert summary.dry_run is True
    assert summary.updates_created == 1
    assert db_session.query(LeadResearchUpdate).count() == 0


def test_research_company_updates_dedupes_existing_update(db_session):
    company = _qualified_company(db_session)

    first = research_company_updates(db_session, company.id)
    second = research_company_updates(db_session, company.id)

    assert first.updates_created == 1
    assert first.crm_profile_updated is True
    assert second.updates_created == 0
    assert second.duplicates_skipped == 1
    assert db_session.query(LeadResearchUpdate).count() == 1


def test_dedupe_fingerprint_and_materiality_are_stable():
    left = dedupe_fingerprint(10, "Expansion: Acme", "https://example.com/a", "Acme expands")
    right = dedupe_fingerprint(10, "Expansion: Acme", "https://example.com/a", "Acme expands")

    assert left == right
    assert materiality_score(update_type="rfp_procurement", signal_strength=0.9, lead_score=90, source_url="x") > 0.9


def test_material_research_result_creates_signal_and_rescores_company(db_session):
    company = Company(name="Warm Buyer Systems LLC", industry="Logistics", source="test")
    db_session.add(company)
    db_session.flush()
    db_session.add(
        Score(
            company_id=company.id,
            automation_score=5,
            labor_pain_score=5,
            expansion_score=5,
            robotics_fit_score=20,
            overall_intent_score=12,
        )
    )
    db_session.commit()
    db_session.refresh(company)

    result = NormalizedResearchResult(
        company_id=company.id,
        update_type="expansion",
        title="Expansion signal: Warm Buyer Systems LLC",
        summary=(
            "Warm Buyer Systems LLC is opening a new distribution center, hiring operations staff, "
            "and evaluating warehouse automation."
        ),
        source_url="https://example.com/warm-buyer-expansion",
        source_domain="example.com",
        detected_at=datetime.now(timezone.utc),
        significance_score=0.95,
        dedupe_fingerprint="research-signal-test",
        payload={},
    )

    signal, created = ensure_signal_for_research_result(db_session, result)
    score_after = rescore_company(db_session, company)
    db_session.commit()

    assert created is True
    assert signal is not None
    assert signal.signal_type == "expansion"
    assert db_session.query(Signal).filter(Signal.company_id == company.id).count() == 1
    assert score_after is not None
    assert score_after > 12


def test_existing_signal_research_result_does_not_duplicate_signal(db_session):
    company = _qualified_company(db_session)
    existing_signal = company.signals[0]
    result = normalize_research_results(company)[0]

    signal, created = ensure_signal_for_research_result(db_session, result)

    assert created is False
    assert signal.id == existing_signal.id
    assert db_session.query(Signal).filter(Signal.company_id == company.id).count() == 1


def test_signal_type_mapping_for_scoring_evidence():
    assert signal_type_for_update("rfp_procurement") == "capex"
    assert signal_type_for_update("deployment") == "automation_intent"


def test_material_research_updates_crm_profile_with_cited_evidence(db_session):
    company = _qualified_company(db_session, name="Profile Buyer Logistics LLC")

    summary = research_company_updates(db_session, company.id)
    db_session.refresh(company)
    crm = company.crm_metadata or {}

    assert summary.crm_profile_updated is True
    assert "warehouse automation" in (crm.get("automation_requirements") or [])
    assert crm.get("quality_flags", {}).get("has_material_research") is True
    evidence = crm.get("research_evidence") or []
    assert len(evidence) == 1
    assert evidence[0]["research_update_id"]
    assert evidence[0]["source_domain"] == "example.com"


def test_crm_profile_update_skips_low_materiality_news(db_session):
    company = Company(name="Quiet Buyer LLC", industry="Logistics", source="test")
    db_session.add(company)
    db_session.flush()
    update = LeadResearchUpdate(
        company_id=company.id,
        update_type="news",
        title="Market news",
        summary="General robotics market commentary.",
        significance_score=0.4,
        status="new",
        dedupe_fingerprint="quiet-news",
    )
    db_session.add(update)
    db_session.flush()

    changed = update_crm_profile_from_research(db_session, company, [update])

    assert changed is False
    assert company.crm_metadata is None

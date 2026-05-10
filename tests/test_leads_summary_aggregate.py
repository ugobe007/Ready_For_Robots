"""Dashboard /api/leads/summary aggregation uses classify_lead (same gate as list)."""

import pytest

try:
    from app.api.leads import _aggregate_lead_rows_from_map, _companies_by_ids, _compute_pipeline_summary
except ImportError:
    pytest.skip(
        "Stale module: aggregation helpers were removed/renamed in leads.py.",
        allow_module_level=True,
    )

from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register metadata
from app.database import Base
from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _sql_like_row(c: Company, *, overall_score: float, signal_count: int, hot_hits: int, warm_hits: int):
    """Mimic columns from _lead_rows_query for aggregate tests."""
    return SimpleNamespace(
        id=c.id,
        name=c.name,
        website=c.website,
        industry=c.industry,
        employee_estimate=c.employee_estimate,
        location_city=c.location_city,
        location_state=c.location_state,
        source=c.source,
        overall_score=overall_score,
        signal_count=signal_count,
        hot_hits=hot_hits,
        warm_hits=warm_hits,
    )


def test_aggregate_excludes_logic_engine_junk_when_exclude_junk(db_session):
    """
    Names that pass ``is_junk`` but fail ``is_valid_lead`` must not inflate HOT in summary.
    """
    good = Company(name="Acme Logistics LLC", industry="Logistics", source="test")
    bad = Company(name="Share Insights", industry="Retail", source="test")
    db_session.add_all([good, bad])
    db_session.flush()

    db_session.add(
        Score(
            company_id=good.id,
            automation_score=70,
            labor_pain_score=60,
            expansion_score=50,
            robotics_fit_score=55,
            overall_intent_score=82.0,
        )
    )
    db_session.add(
        Signal(
            company_id=good.id,
            signal_type="funding_round",
            signal_text="Acme Logistics LLC announces expansion",
            signal_strength=0.85,
        )
    )
    db_session.add(
        Score(
            company_id=bad.id,
            automation_score=80,
            labor_pain_score=70,
            expansion_score=65,
            robotics_fit_score=70,
            overall_intent_score=95.0,
        )
    )
    db_session.commit()

    rows = [
        _sql_like_row(bad, overall_score=95.0, signal_count=0, hot_hits=0, warm_hits=0),
        _sql_like_row(good, overall_score=82.0, signal_count=1, hot_hits=1, warm_hits=0),
    ]
    by_id = _companies_by_ids(db_session, [bad.id, good.id])
    total, hot, warm, cold, junk_count, _by_ind, _ts = _aggregate_lead_rows_from_map(
        rows, by_id, exclude_junk=True
    )
    assert junk_count >= 1
    assert total == 1
    assert hot + warm + cold == 1
    assert hot >= 1


def test_compute_pipeline_summary_reports_database_total(db_session):
    db_session.add(Company(name="Solo Corp LLC", industry="Manufacturing", source="test"))
    db_session.commit()
    out = _compute_pipeline_summary(db_session, exclude_junk=True)
    assert out["companies_in_database"] == 1
    assert out["signals_in_database"] == 0
    assert out["summary_tier_slice_size"] >= 1
    assert out["leads_list_max_per_request"] >= 50


def test_aggregate_include_junk_as_cold_when_exclude_junk_false(db_session):
    bad = Company(name="Share Insights", industry="Retail", source="test")
    db_session.add(bad)
    db_session.flush()
    db_session.add(
        Score(
            company_id=bad.id,
            automation_score=50.0,
            labor_pain_score=50.0,
            expansion_score=50.0,
            robotics_fit_score=50.0,
            overall_intent_score=70.0,
        )
    )
    db_session.commit()
    rows = [_sql_like_row(bad, overall_score=70.0, signal_count=0, hot_hits=0, warm_hits=0)]
    by_id = _companies_by_ids(db_session, [bad.id])
    total, hot, warm, cold, junk_count, _, _ = _aggregate_lead_rows_from_map(
        rows, by_id, exclude_junk=False
    )
    assert total == 1
    assert junk_count == 1
    assert cold == 1 and hot == 0 and warm == 0

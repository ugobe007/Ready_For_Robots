"""Buyer watchlist: search news for named companies; evidence attaches to that company."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.company import Company
from app.models.signal import Signal
from app.services import buyer_watchlist as bw


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(bind=engine)()
    try:
        yield s
    finally:
        s.close()


@pytest.mark.parametrize("title,name,ok", [
    ("Kenco expands robotics program at Ohio DC", "Kenco Logistics", True),
    ("Target pilots shelf-scanning robots", "Target Corporation", True),
    ("New targets for warehouse robots", "Target", False),
    ("UPS deploys robotic unloaders", "UPS", True),
    ("The ups and downs of automation", "UPS", False),
    ("Walmart's automation push", "Walmart", True),
    ("Amazon deploys new robots", "Walmart", False),
])
def test_title_must_name_company(title, name, ok):
    assert bw.title_names_company(title, name) is ok


def test_seed_list_is_real_names():
    from app.services.company_identity import junk_name_reason

    names = bw.seed_names()
    assert len(names) >= 300
    assert not [n for n in names if junk_name_reason(n)]


def _profile(stage, primary=True):
    return {"buyer_readiness": {"stage": stage, "is_primary": primary}}


def test_select_prioritizes_buyer_stages_then_pain_then_seed(db, monkeypatch):
    monkeypatch.setattr(bw, "seed_names", lambda: ["Sysco", "Kroger"])
    prep = Company(name="Chipotle", industry="Restaurants", automation_profile=_profile("preparing"))
    dup = Company(name="Chipotle Mexican Grill", industry="Restaurants", automation_profile=_profile("preparing", False))
    watch = Company(name="Acme Bank", industry="Banking", automation_profile=_profile("watch"))
    pain = Company(name="Lineage", industry="Cold Storage Logistics")
    junk = Company(name="Health Care", industry="Healthcare", automation_profile=_profile("preparing"))
    sysco = Company(name="Sysco Corporation", industry="Food Distribution")
    db.add_all([prep, dup, watch, pain, junk, sysco]); db.flush()
    for _ in range(6):
        db.add(Signal(company_id=pain.id, signal_type="robot_job", signal_strength=0.3,
                      signal_text="ROBOT TASK SIGNAL | Freezer Selector | Picking | pay unknown | specs unknown | open | Lineage"))
    db.commit()
    names = [c.name for c in bw.select_watchlist(db, limit=10)]
    assert names == ["Chipotle", "Lineage", "Sysco Corporation"]   # Kroger not in DB, junk/watch/dup skipped


def test_never_checked_go_before_recently_checked(db, monkeypatch):
    monkeypatch.setattr(bw, "seed_names", lambda: [])
    a = Company(name="Aramark", industry="Food Service", automation_profile=_profile("evaluating"),
                crm_metadata={"watch": {"last_checked": "2026-10-11T00:00:00+00:00"}})
    b = Company(name="Sodexo", industry="Food Service", automation_profile=_profile("evaluating"))
    db.add_all([a, b]); db.commit()
    assert [c.name for c in bw.select_watchlist(db, limit=2)] == ["Sodexo", "Aramark"]


def test_watch_companies_attaches_evidence_and_skips_repeats(db, monkeypatch):
    from app.scrapers.intelligence_news_scraper import IntelligenceNewsScraper

    monkeypatch.setattr(bw, "seed_names", lambda: [])
    c = Company(name="Sysco", industry="Food Distribution", automation_profile=_profile("primed"))
    db.add(c); db.commit()
    articles = [
        {"title": "Sysco pilots autonomous forklifts at Texas DC", "url": "https://n/1",
         "text": "Sysco pilots autonomous forklifts at Texas DC. Rollout planned."},
        {"title": "Amazon deploys new robots", "url": "https://n/2", "text": "Amazon deploys new robots."},
    ]
    scraper = IntelligenceNewsScraper(db=db)
    monkeypatch.setattr(scraper, "_fetch_google_news", lambda q: list(articles))
    monkeypatch.setattr(scraper, "DELAY", 0)
    first = scraper.watch_companies(limit=5)
    rows = db.query(Signal).filter(Signal.company_id == c.id).all()
    assert first["watched"] == 1 and rows
    assert all(r.source_url == "https://n/1" for r in rows)       # Amazon headline not attached to Sysco
    n = len(rows)
    scraper2 = IntelligenceNewsScraper(db=db)
    monkeypatch.setattr(scraper2, "_fetch_google_news", lambda q: list(articles))
    monkeypatch.setattr(scraper2, "DELAY", 0)
    scraper2.watch_companies(limit=5)
    assert db.query(Signal).filter(Signal.company_id == c.id).count() == n   # same URL not saved twice
    db.refresh(c)
    assert c.crm_metadata["watch"]["last_checked"]


def test_discovery_pool_includes_vendor_and_intent_queries():
    from app.scrapers.robot_opportunity_sources import extra_discovery_queries

    q = extra_discovery_queries()
    assert len(q) >= 400
    assert any("Locus Robotics" in x for x in q) and any("labor shortage" in x for x in q)

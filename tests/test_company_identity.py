"""Company identity: junk names never become companies; name variants are one company."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.company import Company
from app.models.signal import Signal
from app.services.company_identity import (
    canonical_company_key,
    find_existing_company,
    group_companies,
    junk_name_reason,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(bind=engine)()
    try:
        yield s
    finally:
        s.close()


@pytest.mark.parametrize("a,b", [
    ("Target", "Target Corporation"), ("Target", "TARGET CORP."), ("Target", "Target Stores"),
    ("Kroger", "The Kroger Co."), ("Walmart Inc", "Wal-Mart Stores"), ("Amazon", "Amazon.com, Inc."),
    ("Sysco", "Sysco Corporation"), ("H-E-B", "HEB"), ("Bank of America", "Bank of America, N.A."),
])
def test_same_company(a, b):
    assert canonical_company_key(a) == canonical_company_key(b)


@pytest.mark.parametrize("a,b", [
    ("Marriott International", "JW Marriott Las Vegas"), ("American Airlines", "American Express"),
    ("Phoenix Logistics", "Phoenix Foods"), ("Bank of America", "Bank of Hawaii"),
])
def test_different_companies(a, b):
    assert canonical_company_key(a) != canonical_company_key(b)


def test_grouping_uses_descriptor_only_when_bare_name_exists():
    rows = [(1, "Kenco Group", None), (2, "Kenco Logistics", None),
            (3, "Phoenix Logistics", None), (4, "Phoenix Foods", None),
            (5, "Kroger", "kroger.com"), (6, "Fred Meyer", "kroger.com"),
            (7, "Acme Inc", "linkedin.com"), (8, "Other Co", "linkedin.com")]
    g = group_companies(rows)
    assert g[1] == g[2]
    assert g[3] != g[4]
    assert g[5] == g[6]
    assert g[7] != g[8]          # shared sites never link companies


@pytest.mark.parametrize("name", ["Hoboken", "Sri Lanka", "How Robots Are Changing Airports",
                                  "Kroger to open new DC", "aHR0cHM6Ly9haXJwb3J0LmV4YW1wbGUuY29tL3Rlcm1pbmFs"])
def test_junk_names(name):
    assert junk_name_reason(name)


@pytest.mark.parametrize("name", ["City of Hoboken", "Target", "Kenco Logistics", "Point to Point Logistics",
                                  "Clark County Department of Aviation", "Bank of America"])
def test_real_names(name):
    assert junk_name_reason(name) is None


def test_find_existing_company_reuses_row(db):
    db.add_all([Company(name="Target Corporation"), Company(name="Kenco Group")])
    db.commit()
    assert find_existing_company(db, "Target").name == "Target Corporation"
    assert find_existing_company(db, "TARGET CORP.").name == "Target Corporation"
    assert find_existing_company(db, "Kenco Logistics").name == "Kenco Group"
    assert find_existing_company(db, "Phoenix Foods") is None


def test_scraper_gate_rejects_junk_before_insert():
    from app.scrapers.base_scraper import BaseScraper

    for name in ("Hoboken", "How Robots Are Changing Airports", "aHR0cHM6Ly9haXJwb3J0LmV4YW1wbGUuY29tL3Rlcm1pbmFs"):
        assert BaseScraper._name_is_valid(name) is False


def test_save_company_reuses_variant_and_blocks_junk(db):
    from app.scrapers.base_scraper import BaseScraper

    class S(BaseScraper):
        def parse(self, html, url):
            pass

    s = S(db=db)
    first = s.save_company({"name": "Target Corporation", "industry": "Retail"})
    again = s.save_company({"name": "Target", "industry": "Retail"})
    assert first is not None and again.id == first.id
    assert s.save_company({"name": "Hoboken"}) is None
    assert db.query(Company).count() == 1


def test_ranking_pools_duplicates_and_lists_once(db):
    from app.services.buyer_ranking import score_companies

    a = Company(name="Target", industry="Retail")
    b = Company(name="Target Corporation", industry="Retail")
    db.add_all([a, b]); db.flush()
    # Each row alone is only Preparing; together they are Evaluating.
    db.add(Signal(company_id=a.id, signal_type="news", signal_strength=0.5,
                  signal_text="Target is modernizing its supply chain"))
    db.add(Signal(company_id=b.id, signal_type="labor_shortage", signal_strength=0.5,
                  signal_text="Target faces store labor shortage"))
    db.commit()
    stages, results = score_companies(db, apply=True)
    assert len(results) == 1 and stages["evaluating"] == 1
    for c in (a, b):
        db.refresh(c)
        assert c.automation_profile["buyer_readiness"]["stage"] == "evaluating"
    assert sum(c.automation_profile["buyer_readiness"]["is_primary"] for c in (a, b)) == 1


# ── Junk names seen in the 2026-10-12 Evaluating/Preparing review ───────────

@pytest.mark.parametrize("name,kind", [
    ("Health Care", "topic"), ("Coming Soon", "topic"), ("Patient Testing Set", "topic"),
    ("Innovative Two-Step Treatment", "topic"), ("Rewiring the future", "sentence"),
    ("Detroit News", "outlet"), ("Washington Post", "outlet"), ("USA Today", "outlet"),
])
def test_review_junk_names(name, kind):
    reason = junk_name_reason(name)
    assert reason and kind in reason.split()[0] or (kind == "outlet" and "outlet" in (reason or "")), reason


def _real_names():
    from pathlib import Path

    path = Path(__file__).parent / "fixtures" / "real_company_names.txt"
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def test_real_company_names_are_never_junk():
    """Real operators, agencies and brands (plus the allowlist) — any hit here demotes a real buyer."""
    from app.services.known_brands import ALLOWLISTED_COMPANY_NAMES

    names = set(_real_names()) | set(ALLOWLISTED_COMPANY_NAMES)
    flagged = {n: junk_name_reason(n) for n in names if junk_name_reason(n)}
    assert not flagged, flagged

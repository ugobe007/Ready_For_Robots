"""Company-level buyer readiness: who is ready to buy or pilot robots."""
import importlib.util
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.company import Company
from app.models.signal import Signal
from app.services.buyer_readiness import assess_company


def posting(title):
    return {"signal_type": "robot_job",
            "signal_text": f"ROBOT TASK SIGNAL | {title} | Task | pay unknown | specs unknown | open | Co"}


def news(text, stype="news"):
    return {"signal_type": stype, "signal_text": text}


@pytest.mark.parametrize("name,signals,stage", [
    ("Clark County", [news("County issues RFP for autonomous floor scrubbing robots at the airport", "rfp_posted")], "buying_now"),
    ("Hilton", [news("Hilton pilots delivery robots at 20 hotels")], "buying_now"),
    ("MGM Resorts", [news("MGM Resorts evaluating vendors for autonomous floor cleaning robots")], "buying_now"),
    ("Sysco", [posting("Order Selector")] * 20 + [posting("Automation Engineer")], "evaluating"),
    ("Walmart", [news("Walmart plans $9 billion investment in automated distribution centers")], "evaluating"),
    ("Kroger", [news("Kroger to open micro-fulfillment center with AutoStore")], "evaluating"),
    ("GEODIS", [posting("Warehouse Associate - work alongside autonomous mobile robots")], "expanding"),
    ("Big Grocer DC", [posting("Order Picker")] * 60 + [posting("Freezer Selector")] * 10, "primed"),
])
def test_stages(name, signals, stage):
    assert assess_company(name, signals).stage == stage


@pytest.mark.parametrize("name,signals", [
    ("Wynn Las Vegas", [posting("Dishwasher")] * 4),                       # a few labor postings ≠ buyer
    ("SaaSCo", [posting("QA Test Automation Engineer"), news("We use marketing automation")]),
    ("Locus Robotics", [news("Locus Robotics raises $100M Series F"), posting("Robotics Technician")]),
])
def test_not_buyers(name, signals):
    r = assess_company(name, signals)
    assert r.stage == "watch", (r.stage, r.why, [e.label for e in r.evidence])


def test_labor_postings_alone_never_exceed_primed():
    r = assess_company("Mega Warehouse Co", [posting("Order Picker")] * 500)
    assert r.stage == "primed" and r.score <= 45


def test_rank_buyers_script_end_to_end(tmp_path, monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    S = sessionmaker(bind=engine)
    db = S()
    a = Company(name="Clark County Department of Aviation", industry="Facilities")
    b = Company(name="Wynn Las Vegas", industry="Hospitality")
    db.add_all([a, b]); db.flush()
    db.add(Signal(company_id=a.id, signal_type="rfp_posted", signal_strength=0.9,
                  signal_text="Request for proposals: autonomous floor scrubbing robots for terminals"))
    db.add(Signal(company_id=b.id, signal_type="robot_job", signal_strength=0.5,
                  signal_text="ROBOT TASK SIGNAL | Dishwasher | Warewash | pay unknown | specs unknown | open | Wynn"))
    db.commit()

    import app.database as database
    monkeypatch.setattr(database, "SessionLocal", lambda: S())
    spec = importlib.util.spec_from_file_location("rank_buyers", Path(__file__).resolve().parents[1] / "scripts" / "rank_buyers.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    out = tmp_path / "buyers.csv"
    monkeypatch.setattr(sys, "argv", ["rank_buyers.py", "--apply", "--csv", str(out)])
    assert mod.main() == 0
    text = out.read_text()
    assert "Clark County Department of Aviation" in text and "buying_now" in text
    assert "Wynn" not in text
    check = S()
    prof = check.get(Company, a.id).automation_profile
    assert prof["buyer_readiness"]["stage"] == "buying_now"


@pytest.mark.parametrize("name", ["Sri Lanka", "Hoboken", "Hoboken, NJ", "Henderson", "Las Vegas", "Dwbrobot", "aHR0cHM6Ly9haXJwb3J0LmV4YW1wbGUuY29tL3Rlcm1pbmFs",
                                  "How Robots Are Changing Airports", "Kroger to open new DC"])
def test_junk_names_are_never_buyers(name):
    r = assess_company(name, [news("County issues RFP for autonomous floor scrubbing robots", "rfp_posted")])
    assert r.stage == "watch" and r.score == 0 or r.why == "robot vendor (supply side)"


@pytest.mark.parametrize("name", ["Kenco Logistics", "GXO", "Japan Airlines", "Point to Point Logistics",
                                  "Bank of America", "Clark County Department of Aviation", "Omni Hotels & Resorts",
                                  "City of Hoboken", "Hoboken University Medical Center", "Providence", "Target"])
def test_real_names_pass(name):
    from app.services.buyer_readiness import buyer_name_problem
    assert buyer_name_problem(name) is None


@pytest.mark.parametrize("stype,stage", [("vendor_selection", "buying_now"), ("pilot_success", "buying_now"),
                                         ("robot_installation", "expanding"), ("automation_intent", "watch")])
def test_typed_signals_count(stype, stage):
    assert assess_company("Sysco", [news("Sysco update", stype)]).stage == stage


# ── Indirect intent and labor pressure (Bob, 2026-10-12) ────────────────────

@pytest.mark.parametrize("name,industry,text,stype,stage", [
    ("Target", "Retail",
     "Target is modernizing its supply chain and redesigning store fulfillment workflows to lower labor costs", "news", "evaluating"),
    ("Darden Restaurants", "Restaurants",
     "Darden cites high turnover and rising wage costs; plans kitchen technology investments", "news", "evaluating"),
    ("Harry Reid International Airport", "Aviation",
     "Airport upgrading terminals and facing staffing shortages among custodial crews", "news", "evaluating"),
    ("Hilton", "Hospitality", "Hilton exploring robots for room service delivery", "news", "evaluating"),
    ("Chipotle", "Restaurants", "Chipotle struggles to hire kitchen staff amid labor shortage", "news", "preparing"),
    ("ABM Industries", "Janitorial", "ABM budgeting for equipment upgrades across facilities", "news", "preparing"),
    ("Prudential Overall Supply", "Commercial Laundry", "Laundry plant faces chronic turnover", "labor_shortage", "preparing"),
    ("Kroger", "Grocery", "Kroger capital plan", "capex", "preparing"),
])
def test_indirect_intent_is_seen(name, industry, text, stype, stage):
    r = assess_company(name, [news(text, stype)], industry=industry)
    assert r.stage == stage, (r.stage, r.why, [e.label for e in r.evidence])


@pytest.mark.parametrize("name,industry,text", [
    ("Acme SaaS", "Software", "Acme modernizing its cloud infrastructure"),
    ("Bank of America", "Banking", "Bank of America cuts costs with efficiency program"),
    ("Big Law LLP", "Legal", "Firm faces associate turnover"),
])
def test_indirect_language_outside_physical_work_stays_watch(name, industry, text):
    assert assess_company(name, [news(text)], industry=industry).stage == "watch"


def test_posting_boilerplate_is_not_company_intent():
    sigs = [posting("Warehouse Associate - optimize workflows, reduce labor costs")] * 3
    assert assess_company("Order Co", sigs, industry="Logistics").stage == "watch"


def test_daily_buyers_report_lists_stages_with_evidence(monkeypatch):
    from app.services import daily_buyers_report as dbr

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    rows = [
        ("Clark County Department of Aviation", "Aviation", "rfp_posted",
         "Request for proposals: autonomous floor scrubbing robots for terminals"),
        ("Target", "Retail", "news",
         "Target is modernizing its supply chain and redesigning store workflows to lower labor costs"),
        ("Chipotle", "Restaurants", "news", "Chipotle struggles to hire kitchen staff amid labor shortage"),
        ("Wynn Las Vegas", "Hospitality", "robot_job",
         "ROBOT TASK SIGNAL | Dishwasher | Warewash | pay unknown | specs unknown | open | Wynn"),
    ]
    for name, ind, st, text in rows:
        c = Company(name=name, industry=ind)
        db.add(c); db.flush()
        db.add(Signal(company_id=c.id, signal_type=st, signal_text=text, signal_strength=0.8,
                      source_url=f"https://example.com/{c.id}"))
    db.commit()

    report = dbr.compose_daily_buyers_report(db, refresh=True)
    assert report["counts"] == {"buying_now": 1, "evaluating": 1, "preparing": 1}
    assert [b["company"] for b in report["buyers"]] == ["Clark County Department of Aviation", "Target", "Chipotle"]
    text = dbr.render_daily_buyers_text(report)
    assert "BUYING NOW" in text and "EVALUATING" in text and "PREPARING" in text
    assert "https://example.com/" in text and "Wynn" not in text
    csv_text = dbr.render_daily_buyers_csv(report)
    assert csv_text.splitlines()[0].startswith("rank,company,stage,score,why,evidence_1")
    assert len(csv_text.splitlines()) == 4
    assert "1 buying now, 1 evaluating, 1 preparing" in dbr._subject(report)


def test_daily_send_uses_buyers_mode_by_default(monkeypatch):
    from app.services import daily_jobs_report as djr

    monkeypatch.delenv("DAILY_REPORT_MODE", raising=False)
    assert djr.daily_report_mode() == "buyers"
    monkeypatch.setenv("DAILY_REPORT_MODE", "jobs")
    assert djr.daily_report_mode() == "jobs"

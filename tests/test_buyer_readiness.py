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
    ("Clark County", [news("County issues RFP for autonomous floor scrubbing robots at the airport", "rfp_posted")], "rfp_open"),
    ("Hilton", [news("Hilton pilots delivery robots at 20 hotels")], "exploring"),
    ("MGM Resorts", [news("MGM Resorts evaluating vendors for autonomous floor cleaning robots")], "rfp_open"),
    ("Sysco", [posting("Order Selector")] * 20 + [posting("Automation Engineer")], "exploring"),
    ("Walmart", [news("Walmart plans $9 billion investment in automated distribution centers")], "exploring"),
    ("Kroger", [news("Kroger to open micro-fulfillment center with AutoStore")], "committed"),
    ("GEODIS", [posting("Warehouse Associate - work alongside autonomous mobile robots")], "committed"),
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
    assert "Clark County Department of Aviation" in text and "rfp_open" in text
    assert "Wynn" not in text
    check = S()
    prof = check.get(Company, a.id).automation_profile
    assert prof["buyer_readiness"]["stage"] == "rfp_open"


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


@pytest.mark.parametrize("stype,stage", [("vendor_selection", "committed"), ("pilot_success", "exploring"),
                                         ("robot_installation", "committed"), ("automation_intent", "watch")])
def test_typed_signals_count(stype, stage):
    assert assess_company("Sysco", [news("Sysco update", stype)]).stage == stage


# ── Indirect intent and labor pressure (Bob, 2026-10-12) ────────────────────

@pytest.mark.parametrize("name,industry,text,stype,stage", [
    ("Target", "Retail",
     "Target is modernizing its supply chain and redesigning store fulfillment workflows to lower labor costs", "news", "preparing"),
    ("Darden Restaurants", "Restaurants",
     "Darden cites high turnover and rising wage costs; plans kitchen technology investments", "news", "preparing"),
    ("Harry Reid International Airport", "Aviation",
     "Airport upgrading terminals and facing staffing shortages among custodial crews", "news", "preparing"),
    ("Hilton", "Hospitality", "Hilton exploring robots for room service delivery", "news", "exploring"),
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
    assert report["counts"] == {"rfp_open": 1, "expanding": 0, "exploring": 0, "preparing": 2}
    assert [b["company"] for b in report["buyers"]] == ["Clark County Department of Aviation", "Chipotle", "Target"]
    text = dbr.render_daily_buyers_text(report)
    assert "RFP OPEN" in text and "PREPARING" in text and "Likely next" in text
    assert "https://example.com/" in text and "Wynn" not in text
    csv_text = dbr.render_daily_buyers_csv(report)
    assert csv_text.splitlines()[0].startswith("rank,company,stage,score,why,open_categories,already_has,likely_next")
    assert len(csv_text.splitlines()) == 4
    assert "1 RFPs open, 0 expanding, 0 exploring, 2 preparing" in dbr._subject(report)


def test_daily_send_uses_buyers_mode_by_default(monkeypatch):
    from app.services import daily_jobs_report as djr

    monkeypatch.delenv("DAILY_REPORT_MODE", raising=False)
    assert djr.daily_report_mode() == "buyers"
    monkeypatch.setenv("DAILY_REPORT_MODE", "jobs")
    assert djr.daily_report_mode() == "jobs"


# ── Routine events alone are not buying evidence (2026-10-12 review) ─────────

@pytest.mark.parametrize("name,industry,sigs", [
    ("Uline", "Distribution", [("Uline hiring event", "news"), ("Uline names director of distribution", "strategic_hire"),
                               ("Uline opens new distribution center", "expansion")]),
    ("Dollar General", "Retail", [("Dollar General to open 800 new stores", "expansion")]),
    ("Acme SaaS", "Software", [("Acme announces technology investment in cloud", "news")]),
])
def test_routine_events_alone_stay_watch(name, industry, sigs):
    r = assess_company(name, [news(t, st) for t, st in sigs], industry=industry)
    assert r.stage == "watch", (r.stage, r.why)


@pytest.mark.parametrize("name,industry,text,stage", [
    ("Merlin Entertainments", "Entertainment",
     "Merlin commits €400M resort program, modernizing parks and budgeting for autonomous delivery", "exploring"),
    ("Caesars Entertainment", "Casinos", "Caesars $500M property modernization includes automation technology", "exploring"),
    ("Wynn Resorts", "Casinos",
     "Wynn pilots robotic cocktail delivery; housekeeping exploring automation as operation is 29% understaffed", "exploring"),
])
def test_review_real_buyers_hold(name, industry, text, stage):
    assert assess_company(name, [news(text)], industry=industry).stage == stage


@pytest.mark.parametrize("name", ["Health Care", "Detroit News", "Coming Soon", "Rewiring the future"])
def test_review_junk_names_are_watch(name):
    r = assess_company(name, [news("Chain struggles to hire kitchen staff amid labor shortage"),
                              news("pilots delivery robots")], industry="Restaurants")
    assert r.stage == "watch" and r.score == 0


# ── Opportunity map: sell into workflows, not companies (Bob, 2026-10-12) ───

def test_disney_has_cleaning_robots_but_doors_stay_open():
    sigs = [news("Disney deploys floor-cleaning robots at EPCOT and Magic Kingdom."),
            news("Disney plans to add more cleaning robots across its parks and is exploring restroom sanitizing robots."),
            news("Disney is testing delivery robots at Disney Springs for food delivery.")]
    r = assess_company("Disney Parks", sigs, industry="Theme Parks")
    assert r.stage == "expanding"
    status = {o["category"]: o["status"] for o in r.opportunities["open"]}
    assert status == {"cleaning": "expanding", "restroom_sanitizing": "exploring", "delivery_service": "piloting"}
    assert {"entertainment", "food_prep"} <= {p["category"] for p in r.opportunities["predicted_next"]}
    assert set(r.opportunities["matches_prediction"]) == set(status)


def test_robots_bought_and_nothing_new_is_committed_not_a_lead():
    r = assess_company("Kroger", [news("Kroger deploys Symbotic robots at all DCs")], industry="Grocery")
    assert r.stage == "committed"
    assert r.opportunities["already_has"][0]["vendors"] == ["Symbotic"]


def test_committed_buyer_under_pressure_reopens_for_other_workflows():
    r = assess_company("Kroger", [news("Kroger deploys Symbotic robots at all DCs"),
                                  news("Kroger faces store labor shortage", "labor_shortage")], industry="Grocery")
    assert r.stage == "preparing" and "proven robot buyer" in r.why
    assert "warehouse_amr" not in {p["category"] for p in r.opportunities["predicted_next"]}


def test_rfp_outranks_everything():
    r = assess_company("Clark County Department of Aviation",
                       [news("Airport deploys security robots"),
                        news("Clark County issues RFP for autonomous floor scrubbing robots at terminals", "rfp_posted")],
                       industry="Aviation")
    assert r.stage == "rfp_open" and "budget confirmed" in r.why


def test_loose_automation_interest_type_needs_robot_words():
    r = assess_company("Sysco", [news("Sysco quarterly results", "automation_interest")], industry="Food Distribution")
    assert r.stage == "watch"

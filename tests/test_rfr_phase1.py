import importlib.util
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.models.company import Company
from app.models.signal import Signal
from app.services.buyer_opportunity import backfill_report as br
from app.services.buyer_opportunity import seed_import as si
from app.services.buyer_opportunity.tables import RFR_TABLES
from scripts import rfr_import_seed

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "versions" / "rfr0a1b2c3d4_add_rfr_buyer_opportunity_tables.py"
HEADER = ",".join(si.SEED_COLUMNS)


def _migration():
    spec = importlib.util.spec_from_file_location("rfr_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(conn, step):
    with Operations.context(MigrationContext.configure(conn)):
        getattr(_migration(), step)()


@pytest.fixture
def engine(tmp_path):
    eng = sa.create_engine(f"sqlite:///{tmp_path / 'copy.db'}")
    with eng.begin() as conn:
        Company.__table__.create(conn)
        Signal.__table__.create(conn)
        _run(conn, "upgrade")
    return eng


def _write_seed(tmp_path, *rows):
    path = tmp_path / "seed.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n")
    return path


def _dump(conn, tables=RFR_TABLES):
    return {t.name: [dict(r) for r in conn.execute(sa.select(t).order_by(t.c.id)).mappings()] for t in tables}


def _dump_existing(conn):
    return {
        name: [tuple(r) for r in conn.execute(sa.text(f"SELECT * FROM {name} ORDER BY id"))]
        for name in ("companies", "signals")
    }


SEED = (
    'EXAMPLE Resort & Casino (delete this row),example.com,casino|hotel,Las Vegas,NV,A,cleaning,cleaning:VendorName,x',
    'Wynn Las Vegas,https://www.wynnlasvegas.com/,casino|hotel|bar_nightclub,Las Vegas,NV,A,'
    'cleaning|delivery_transport|food_beverage_prep,cleaning:Avidbots,',
    'Sysco Corporation,sysco.com,warehouse_distribution|logistics_parcel,Houston,TX,b,picking_packing_palletizing,,',
    'Valley Surgery Center LLC,,surgery_center,Henderson,NV,,delivery_transport,,no website',
    'Richtech Robotics,richtechrobotics.com,restaurant,Las Vegas,NV,C,food_beverage_prep,,robot maker',
    'Bad Row,bad.example,space_station,Reno,NV,A,teleportation,cleaning,',
    'Wynn duplicate,wynnlasvegas.com,casino,Las Vegas,NV,A,,,',
)


def test_migration_matches_core_tables_and_downgrades_only_rfr(engine):
    insp = sa.inspect(engine)
    for table in RFR_TABLES:
        reflected = {c["name"]: c for c in insp.get_columns(table.name)}
        assert list(reflected) == [c.name for c in table.columns]
        for col in table.columns:
            assert reflected[col.name]["nullable"] == col.nullable, (table.name, col.name)
    unique = {i["name"] for i in insp.get_indexes("rfr_buyers") if i["unique"]}
    assert {"ux_rfr_buyers_website_domain", "ux_rfr_buyers_name_normalized"} <= unique
    with engine.begin() as conn:
        _run(conn, "downgrade")
    assert set(sa.inspect(engine).get_table_names()) == {"companies", "signals"}


def test_seed_import_twice_gives_identical_rows(engine, tmp_path):
    path = _write_seed(tmp_path, *SEED)
    with engine.begin() as conn:
        conn.execute(Company.__table__.insert().values(id=7, name="Sysco", website_domain="sysco.com", industry="Food & Beverage Distribution"))
        before_existing = _dump_existing(conn)
        first = si.import_seed(conn, path)
    with engine.begin() as conn:
        after_first = _dump(conn)
    with engine.begin() as conn:
        second = si.import_seed(conn, path)
        assert _dump_existing(conn) == before_existing
    with engine.begin() as conn:
        assert _dump(conn) == after_first

    assert first.buyers == {"inserted": 4, "updated": 0, "unchanged": 0}
    assert second.buyers == {"inserted": 0, "updated": 0, "unchanged": 4}
    assert second.writes == 0 and second.industries_inserted == 0
    assert first.skipped_example == [2]
    assert [r["line"] for r in first.rejected] == [7, 8]
    assert first.robot_makers == ["Richtech Robotics"]
    assert first.company_links == {"linked": 1, "none": 3, "ambiguous": 0}

    buyers = {b["name"]: b for b in after_first["rfr_buyers"]}
    assert buyers["Wynn Las Vegas"]["website_domain"] == "wynnlasvegas.com"
    assert buyers["Sysco Corporation"]["company_id"] == 7 and buyers["Sysco Corporation"]["priority"] == "B"
    assert buyers["Valley Surgery Center LLC"]["website_domain"] is None
    assert buyers["Valley Surgery Center LLC"]["name_normalized"] == "valley surgery center"
    assert buyers["Richtech Robotics"]["is_robot_maker"] is True
    assert {b["source"] for b in buyers.values()} == {"bob_seed"}
    assert all(i["source"] == "bob_seed" and i["source_url"] is None for i in after_first["rfr_buyer_industries"])

    wynn = buyers["Wynn Las Vegas"]["id"]
    workflows = {w["workflow"]: w for w in after_first["rfr_workflows"] if w["buyer_id"] == wynn}
    assert workflows["cleaning"]["status"] == "committed"
    assert workflows["cleaning"]["committed_vendor"] == "Avidbots"
    assert workflows["cleaning"]["status_note"] == si.DEPLOYMENT_NOTE
    assert workflows["delivery_transport"]["status"] == "unknown"
    assert after_first["rfr_signals"] == [] and after_first["rfr_opportunities"] == []


def test_changed_seed_updates_only_changed_rows(engine, tmp_path):
    with engine.begin() as conn:
        si.import_seed(conn, _write_seed(tmp_path, SEED[2]))
    changed = SEED[2].replace(",TX,b,", ",TX,A,")
    with engine.begin() as conn:
        result = si.import_seed(conn, _write_seed(tmp_path, changed))
        priority = conn.execute(sa.text("SELECT priority FROM rfr_buyers")).scalar_one()
    assert result.buyers == {"inserted": 0, "updated": 1, "unchanged": 0}
    assert priority == "A"


def test_rejections_name_the_problem():
    rows, result = si.parse_seed_rows([HEADER + "\n", SEED[5] + "\n", "Home Robots Co,home.example,residential_consumer,,,,,,\n"])
    assert rows == []
    errors = [e for r in result.rejected for e in r["errors"]]
    assert "unknown industry 'space_station'" in errors
    assert "unknown workflow 'teleportation'" in errors
    assert "known_deployments item 'cleaning' is not workflow:vendor" in errors
    assert "'residential_consumer' is never a buyer industry" in errors


def test_missing_columns_fail_loudly():
    with pytest.raises(ValueError, match="missing columns"):
        si.parse_seed_rows(["company_name,website\n"])


@pytest.mark.parametrize("raw,expected", [
    ("https://www.Wynn.com/path?q=1", "wynn.com"),
    ("sysco.com", "sysco.com"),
    ("WWW.example.org/", "example.org"),
    ("", None),
])
def test_normalize_domain(raw, expected):
    assert si.normalize_domain(raw) == expected


def test_script_dry_run_writes_nothing(engine, tmp_path, capsys):
    path = _write_seed(tmp_path, SEED[1])
    code = rfr_import_seed.main(["--database-url", str(engine.url), "--csv", str(path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["applied"] is False and out["writes"] > 0
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT count(*) FROM rfr_buyers")).scalar_one() == 0
    rfr_import_seed.main(["--database-url", str(engine.url), "--csv", str(path), "--apply"])
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT count(*) FROM rfr_buyers")).scalar_one() == 1


def test_synonyms_file_is_valid():
    synonyms = br.load_synonyms()
    assert synonyms["food & beverage distribution"]["industries"] == ["warehouse_distribution", "logistics_parcel"]
    hospitality = synonyms["hospitality"]
    assert hospitality["status"] == "company_check"
    assert hospitality["candidates"] == ["hotel", "restaurant"] and hospitality["default"] == ["hotel"]
    assert synonyms["food service"]["industries"] == ["restaurant"]
    assert synonyms["e-commerce & logistics"]["industries"] == ["warehouse_distribution"]
    assert synonyms["healthcare"]["default"] == [] and synonyms["automotive"]["default"] == []
    assert synonyms["food service & facilities"]["candidates"] == ["facility_services"]
    assert synonyms["unknown"]["status"] == "ignore"
    assert not any(e["status"] == "needs_bob" for e in synonyms.values())


SYNONYM_HEADER = ",".join(br.SYNONYM_COLUMNS)


@pytest.mark.parametrize("row,error", [
    ("Hospitality,hotel|restaurant,casino,yes,", "not among candidate_industries"),
    ("Hospitality,,,yes,", "needs candidate_industries"),
    ("Hospitality,hotel|restaurant,,no,", "need needs_company_check = yes"),
    ("Hospitality,hotel,hotel,maybe,", "not yes or no"),
    ("Homes,residential_consumer,residential_consumer,no,", "never a buyer industry"),
    ("Space,space_station,space_station,no,", "unknown industries"),
])
def test_synonym_rows_are_validated(tmp_path, row, error):
    path = tmp_path / "synonyms.csv"
    path.write_text(f"{SYNONYM_HEADER}\n{row}\n")
    with pytest.raises(ValueError, match=error):
        br.load_synonyms(path)


def test_backfill_report_counts_by_industry_and_writes_nothing(engine):
    companies = [
        dict(id=1, name="Marriott", website_domain="marriott.com", industry="Hospitality (Hotels)"),
        dict(id=2, name="Hilton", website_domain="hilton.com", industry="  hospitality (hotels) "),
        dict(id=3, name="Sysco", website_domain="sysco.com", industry="Food & Beverage Distribution"),
        dict(id=4, name="Mystery Co", industry="Hospitality"),
        dict(id=5, name="Odd Co", industry="Space Logistics"),
        dict(id=6, name="Blank Co", industry=None),
        dict(id=7, name="Richtech Robotics", website_domain="richtechrobotics.com", industry="Food Service"),
        dict(id=8, name="Postings Only Inc", industry="Manufacturing"),
        dict(id=9, name="Indeed-sourced Co", industry="Manufacturing", source="job_board"),
        dict(id=10, name="Customer CRM row", industry="Manufacturing", tenant_id="t1"),
        dict(id=11, name="Cruise Co", industry="Cruise Lines"),
        dict(id=12, name="Inn Co", industry="hospitality"),
        dict(id=13, name="Lodge Co", industry="Hospitality"),
        dict(id=14, name="Resort Co", industry="Hospitality"),
    ]
    with engine.begin() as conn:
        for company in companies:
            conn.execute(Company.__table__.insert().values(**company))
        conn.execute(Signal.__table__.insert(), [
            dict(company_id=8, signal_type="job_posting", signal_text="Hiring", signal_strength=0.2),
            dict(company_id=1, signal_type="job_posting", signal_text="Hiring", signal_strength=0.2),
            dict(company_id=1, signal_type="news", signal_text="Robot pilot", signal_strength=0.6),
        ])
        before = _dump_existing(conn)
    with engine.connect() as conn:
        trans = conn.begin()
        report = br.build_backfill_report(conn)
        trans.rollback()
        assert _dump_existing(conn) == before
        assert conn.execute(sa.text("SELECT count(*) FROM rfr_buyers")).scalar_one() == 0

    assert report["writes"] == 0
    assert report["counts"] == {
        "companies_read": 14, "excluded_tenant_crm_rows": 1, "excluded_robot_makers": 1,
        "skipped_job_posting_only": 2, "mapped": 4, "needs_company_check": 4, "unmapped": 1,
        "unmapped_blank_industry": 1,
    }
    assert report["mapped_by_industry"] == {"hotel": 2, "warehouse_distribution": 1, "logistics_parcel": 1, "ships_maritime": 1}
    assert report["mapped_by_pilot_group"] == {
        "1. Warehouse, logistics, 3PL": 1, "3. Hotels and casinos": 2, "hidden (not a pilot industry)": 1,
    }
    assert report["needs_company_check_by_raw_value"] == {"Hospitality": 4}
    assert report["needs_company_check_examples"] == {"Hospitality": ["Mystery Co", "Inn Co", "Lodge Co"]}
    assert report["company_check_review"] == []
    assert report["unmapped_by_raw_value"] == {"Space Logistics": 1}
    assert report["robot_makers_excluded"] == ["Richtech Robotics"]
    md = br.render_markdown(report)
    assert "nothing written" in md and "- hotel: 2" in md
    assert "- Hospitality: 4 (e.g. Mystery Co, Inn Co, Lodge Co)" in md

    checks = {
        12: {"status": "decided", "industries": ["restaurant"]},
        13: {"status": "review", "reason": "no pick had a quote found on the site"},
    }
    with engine.connect() as conn:
        trans = conn.begin()
        report = br.build_backfill_report(conn, company_checks=checks)
        trans.rollback()
    assert report["counts"]["mapped_by_company_check"] == 1
    assert report["counts"]["company_check_review"] == 1
    assert report["counts"]["needs_company_check"] == 2
    assert report["mapped_by_industry"]["restaurant"] == 1
    assert report["company_check_review"] == [{
        "company_id": 13, "name": "Lodge Co", "raw_value": "Hospitality", "candidates": ["hotel", "restaurant"],
        "suggestion": ["hotel"], "reason": "no pick had a quote found on the site",
    }]
    assert "- Lodge Co (Hospitality): suggest hotel; candidates hotel, restaurant." in br.render_markdown(report)

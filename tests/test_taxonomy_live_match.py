"""Taxonomy URL match stays off by default and does not change existing tables."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.company import Company
from app.models.company_taxonomy_industry import CompanyTaxonomyIndustry
from app.services.taxonomy_buyer_match import match_products_to_buyers, readiness_from_signals
from app.services.taxonomy_industry_map import (
    buyers_from_taxonomy_table,
    map_company_industries,
    write_taxonomy_industries,
)
from app.services.taxonomy_industry_synonyms import classify_industry
from app.services.taxonomy_live_match import compose_taxonomy_job_search, taxonomy_match_enabled


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("TAXONOMY_MATCH_ENABLED", raising=False)
    assert taxonomy_match_enabled() is False
    monkeypatch.setenv("TAXONOMY_MATCH_ENABLED", "1")
    assert taxonomy_match_enabled() is True


def test_synonym_table_maps_exact_labels_and_lists_the_rest():
    assert classify_industry("Food Service") == "restaurant"
    assert classify_industry("Automotive & Manufacturing") == "manufacturing"
    assert classify_industry("Healthcare (Hospital Systems)") == "hospital"
    assert classify_industry("Logistics & Warehousing (3PL)") == "3pl"
    assert classify_industry("Datacenters") == "data_center"
    assert classify_industry("Logistics") is None
    assert classify_industry("Hospitality") is None
    assert classify_industry("Unknown") is None
    assert classify_industry("Food Service & Hospitality") is None


def test_people_posting_readiness_is_not_a_buyer_signal():
    assert readiness_from_signals("primed", "44 open postings for work robots do today")[1] == "job_board"
    assert readiness_from_signals("evaluating", "hiring automation talent / automation program stated")[1] == "job_board"
    readiness, kind = readiness_from_signals("buying_now", "tender, pilot or vendor selection on record")
    assert readiness == "rfp"
    assert kind == "company"
    assert readiness_from_signals("expanding", "already operates robots — next site or next workflow")[0] == "expanding"


def _product(industries, function="cleaning"):
    return {
        "product_name": "Neo",
        "company": "Avidbots",
        "primary_function": {"value": function},
        "secondary_functions": [],
        "industries": [{"value": item} for item in industries],
    }


def test_match_joins_industry_and_function_and_ranks_rfp_first():
    buyers = [
        {
            "company_id": 1,
            "company_name": "Expanding Hotel",
            "taxonomy_industries": ["hotel"],
            "functions": ["cleaning"],
            "readiness": "expanding",
            "source_kind": "company",
        },
        {
            "company_id": 2,
            "company_name": "RFP Hotel",
            "taxonomy_industries": ["hotel"],
            "functions": ["cleaning"],
            "readiness": "rfp",
            "source_kind": "sam_gov",
        },
        {
            "company_id": 3,
            "company_name": "Indeed Hotel",
            "taxonomy_industries": ["hotel"],
            "functions": ["cleaning"],
            "readiness": "rfp",
            "source_kind": "job_board",
        },
        {
            "company_id": 4,
            "company_name": "Picking Only",
            "taxonomy_industries": ["hotel"],
            "functions": ["picking_packing_palletizing"],
            "readiness": "rfp",
            "source_kind": "company",
        },
        {
            "company_id": 5,
            "company_name": "Untagged Hotel",
            "taxonomy_industries": ["hotel"],
            "functions": [],
            "readiness": "rfp",
            "source_kind": "company",
        },
    ]
    result = match_products_to_buyers([_product(["hotel"])], buyers)
    names = [job["company_name"] for job in result["jobs"]]
    assert names[0] == "RFP Hotel"
    assert "Indeed Hotel" not in names
    assert "Picking Only" not in names
    assert "Untagged Hotel" in names
    untagged = next(job for job in result["jobs"] if job["company_name"] == "Untagged Hotel")
    assert untagged["function_matched"] is False
    assert result["jobs"][0]["function_matched"] is True
    assert result["matcher"] == "taxonomy_v4"
    doubled = match_products_to_buyers(
        [_product(["hotel"], "cleaning"), _product(["hotel"], "cleaning")],
        buyers[:1],
    )
    assert [job["company_name"] for job in doubled["jobs"]] == ["Expanding Hotel"]


def test_write_maps_a_new_table_and_leaves_the_company_row_alone():
    engine = create_engine("sqlite://")
    Company.__table__.create(engine)
    CompanyTaxonomyIndustry.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    company = Company(name="Sodexo USA", industry="Food Service", website="https://us.sodexo.com")
    other = Company(name="SoftBank", industry="Datacenters", website="https://www.softbank.jp/en/")
    ambiguous = Company(name="Some Logistics Co", industry="Logistics", website="https://example.com")
    session.add_all([company, other, ambiguous])
    session.flush()
    planned = map_company_industries(
        [
            {"id": company.id, "name": company.name, "industry": company.industry, "readiness": "rfp", "source_kind": "company"},
            {"id": other.id, "name": other.name, "industry": other.industry, "readiness": "expanding", "source_kind": "company"},
            {"id": ambiguous.id, "name": ambiguous.name, "industry": ambiguous.industry},
        ]
    )
    assert [row["company_name"] for row in planned["unmapped"]] == ["Some Logistics Co"]
    written = write_taxonomy_industries(session, planned["mapped"])
    session.commit()
    session.refresh(company)
    assert written == 2
    assert company.industry == "Food Service"
    stored = buyers_from_taxonomy_table(session)
    assert {row["company_name"] for row in stored} == {"Sodexo USA", "SoftBank"}
    session.close()


def test_compose_uses_the_extractor_and_not_the_old_corpus():
    def fake_extract(url, text, hint):
        assert "gritt" in url
        assert "cleaning robot" in text
        return {
            "products": [
                {
                    "company": "Gritt",
                    "product_name": "Gritt",
                    "offering_type": {"value": "robot_product"},
                    "form": {"value": "mobile_manipulator"},
                    "primary_class": {"value": "service_robot"},
                    "primary_function": {"value": "cleaning"},
                    "secondary_functions": [],
                    "industries": [{"value": "commercial_building"}],
                }
            ],
            "page": {"page_type": {"value": "manufacturer_product_page"}},
            "extraction_metadata": {"prompt_version": "v4"},
        }

    out = compose_taxonomy_job_search(
        "https://gritt.ai",
        page_text="The Gritt cleaning robot scrubs floors in commercial buildings.",
        buyers=[
            {
                "company_id": 9,
                "company_name": "RFP Facilities",
                "taxonomy_industries": ["commercial_building"],
                "functions": ["cleaning"],
                "readiness": "rfp",
                "source_kind": "sam_gov",
            }
        ],
        unmapped=[{"company_name": "Mystery Co", "industry_text": "Hospitality"}],
        extract=fake_extract,
    )
    assert out["matcher"] == "taxonomy_v4"
    assert out["jobs"][0]["company_name"] == "RFP Facilities"
    assert out["taxonomy_products"][0]["primary_function"] == "cleaning"
    assert out["unmapped_count"] == 1


def test_find_handler_keeps_the_old_matcher_when_the_flag_is_off(monkeypatch):
    from app.api.robot_job_search import RobotJobSearchIn, post_robot_job_search

    monkeypatch.delenv("TAXONOMY_MATCH_ENABLED", raising=False)
    called = {}

    def old_compose(*_a, **_k):
        called["old"] = True
        return {
            "company_name": "Gritt",
            "robot_name": "Gritt",
            "robot_class": None,
            "capabilities": [],
            "job_count": 0,
            "profile": {},
            "jobs": [],
        }

    def new_compose(*_a, **_k):
        called["new"] = True
        return old_compose()

    monkeypatch.setattr("app.api.robot_job_search.compose_robot_job_search", old_compose)
    monkeypatch.setattr("app.api.robot_job_search.compose_taxonomy_job_search", new_compose)
    monkeypatch.setattr("app.api.robot_job_search.record_shadow_observation", lambda *a, **k: None)
    monkeypatch.setattr(
        "app.services.robot_submission_service.record_robot_submission",
        lambda *a, **k: None,
    )
    result = post_robot_job_search(
        RobotJobSearchIn(url="https://gritt.ai"),
        db=None,
        x_correlation_id=None,
    )
    assert called == {"old": True}
    assert result["matcher"] if "matcher" in result else result["robot_name"] == "Gritt"

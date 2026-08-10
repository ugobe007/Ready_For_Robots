"""Sprint 1 — sources, facilities, primitives, provenance utility."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa: F401
from app.domain.enums import load_primitives_ontology
from app.models.company import Company
from app.models.facility import Facility
from app.models.primitive import Primitive
from app.models.source import Source
from app.services.truth import append_claim, provenanced, upsert_source


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    # Seed primitives like migration
    for p in load_primitives_ontology()["primitives"]:
        session.add(
            Primitive(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"rfr:primitive:{p['code']}")),
                code=p["code"],
                category=p["category"],
                name=p["name"],
                ontology_version="1.0.0",
            )
        )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_provenanced_unknown_zeros_confidence():
    envelope = provenanced("x", truth_state="unknown", confidence=0.9)
    assert envelope["truth_state"] == "unknown"
    assert envelope["confidence"] == 0.0


def test_observed_claim_requires_excerpt(db_session):
    with pytest.raises(ValueError, match="excerpt"):
        append_claim(
            db_session,
            entity_type="robot_profile",
            entity_id="r1",
            field_path="payload_max_kg",
            value=1500,
            truth_state="observed",
            confidence=0.9,
            excerpt=None,
        )


def test_source_and_claim_lineage(db_session):
    source = upsert_source(
        db_session,
        source_type="product_page",
        url="https://acme.example/forklift",
        content_hash="abc",
        title="AutoFork",
    )
    claim = append_claim(
        db_session,
        entity_type="robot_profile",
        entity_id="profile-1",
        field_path="payload_max_kg",
        value=1500,
        truth_state="observed",
        confidence=0.85,
        source_id=source.id,
        source_type="product_page",
        source_url=source.url,
        excerpt="Payload capacity 1500 kg",
    )
    db_session.commit()
    assert db_session.query(Source).count() == 1
    assert claim.source_id == str(source.id)
    # dedupe
    again = upsert_source(
        db_session,
        source_type="product_page",
        url="https://acme.example/forklift",
        content_hash="abc",
    )
    assert again.id == source.id


def test_facility_under_company_not_hq_collapse(db_session):
    company = Company(name="Riviana Foods", location_city="Houston", location_state="TX")
    db_session.add(company)
    db_session.flush()
    memphis = Facility(
        id=str(uuid.uuid4()),
        company_id=company.id,
        name="Memphis Plant",
        city="Memphis",
        state="TN",
        normalized_address="memphis-tn-plant",
        location_precision="exact",
        truth_state="inferred",
        confidence=0.6,
    )
    db_session.add(memphis)
    db_session.commit()
    assert memphis.city != company.location_city
    assert db_session.query(Facility).filter_by(company_id=company.id).count() == 1


def test_primitives_seeded(db_session):
    assert db_session.query(Primitive).count() >= 20
    assert db_session.query(Primitive).filter_by(code="eng.acquire_pallet_floor").one()

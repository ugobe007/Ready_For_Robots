"""Robot catalog hierarchy + Tier-1 seed gates."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa: F401
from app.domain.enums import assert_commercial_maturity, commercial_maturity_states
from app.models.robot_catalog import Manufacturer, RobotConfiguration, RobotFamily, RobotModel
from scripts.seed_robot_catalog_tiers import upsert_catalog

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "docs" / "calibration"
TIER1 = CAL / "tier1_oem_catalog_v1.json"
TIER2 = CAL / "tier2_oem_stubs_v1.json"


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
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_commercial_maturity_enum_locked():
    expected = {
        "concept",
        "prototype",
        "pilot",
        "commercial",
        "production",
        "discontinued",
        "unknown",
    }
    assert commercial_maturity_states() == expected
    assert assert_commercial_maturity("COMMERCIAL") == "commercial"
    with pytest.raises(ValueError):
        assert_commercial_maturity("beta")


def test_tier1_seed_file_counts():
    data = json.loads(TIER1.read_text())
    manufacturers = data["manufacturers"]
    assert len(manufacturers) == 30
    models = [m for mfr in manufacturers for fam in mfr["families"] for m in fam["models"]]
    assert 50 <= len(models) <= 75
    slugs = [m["slug"] for m in models]
    assert len(slugs) == len(set(slugs))
    for m in models:
        assert_commercial_maturity(m["commercial_maturity"])


def test_tier2_seed_has_no_fake_capabilities():
    data = json.loads(TIER2.read_text())
    assert len(data["manufacturers"]) >= 20
    for mfr in data["manufacturers"]:
        for fam in mfr["families"]:
            for model in fam["models"]:
                assert model.get("capability_stubs") in (None, [])
                assert model.get("work_envelope_stubs") in (None, [])
                assert model["commercial_maturity"] == "unknown"


def test_upsert_catalog_is_idempotent(db_session):
    payload = json.loads(TIER1.read_text())
    first = upsert_catalog(db_session, payload)
    db_session.commit()
    assert first["manufacturers"] == 30
    assert first["models"] >= 50
    second = upsert_catalog(db_session, payload)
    db_session.commit()
    assert second["manufacturers"] == 0
    assert second["models"] == 0
    assert db_session.query(Manufacturer).count() == 30
    assert db_session.query(RobotModel).filter(RobotModel.calibration_tier == 1).count() >= 50
    assert db_session.query(RobotFamily).count() >= 30
    assert db_session.query(RobotConfiguration).count() >= 50


def test_manufacturer_family_model_uniqueness(db_session):
    payload = json.loads(TIER1.read_text())
    upsert_catalog(db_session, payload)
    db_session.commit()
    mir = db_session.query(Manufacturer).filter(Manufacturer.slug == "mir").one()
    models = db_session.query(RobotModel).filter(RobotModel.manufacturer_id == mir.id).all()
    assert {m.slug for m in models} >= {"mir-250", "mir-600", "mir-1350"}
    digit = db_session.query(RobotModel).filter(RobotModel.slug == "agility-digit").one()
    assert digit.primary_class == "humanoid"
    assert "handle_tote" in {c["key"] for c in digit.capability_stubs}

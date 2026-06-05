"""Tests for SCOUT discovery agent helpers."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401
from app.services.scout_discovery_agent import (
    _category_key,
    _recommended_action,
    _tier_from_score,
    discover_prospects,
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
        Base.metadata.drop_all(bind=engine)


def test_category_key_aliases():
    assert _category_key("amr") == "amr"
    assert _category_key("Warehouse / AMR") == "amr"
    assert _category_key("  healthcare ") == "healthcare"
    assert _category_key("unknown_slug_xyz") is None


def test_tier_from_score():
    assert _tier_from_score(85) == "HOT"
    assert _tier_from_score(55) == "WARM"
    assert _tier_from_score(20) == "COLD"


def test_recommended_action_hot_rfp():
    action = _recommended_action("HOT", ["rfp_posted", "capex"])
    assert "RFP" in action or "procurement" in action.lower()


def test_discover_prospects_empty_db(db_session):
    """With empty test DB, discover returns structure without error."""
    result = discover_prospects(
        db_session,
        robot_category="amr",
        territory="Texas",
        limit=5,
    )
    assert "prospects" in result
    assert "summary" in result
    assert isinstance(result["prospects"], list)

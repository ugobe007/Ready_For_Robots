"""POST /api/admin/import/companies — uses is_valid_lead (same gate as scrapers)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register metadata
from app.api.admin import CompanyImportPayload, CompanyRecord, import_companies
from app.database import Base
from app.services.company_validator import is_valid_lead


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


def test_import_accepts_valid_company(db_session):
    payload = CompanyImportPayload(
        companies=[
            CompanyRecord(name="Acme Robotics Inc", industry="Manufacturing", source="test"),
        ]
    )
    out = import_companies(payload, db_session)
    assert out["added"] == 1
    assert out["skipped"] == 0
    assert "Acme Robotics Inc" in out["names"]


def test_import_rejects_invalid_name(db_session):
    bad = "Equipment"
    ok, _ = is_valid_lead(bad)
    assert ok is False

    payload = CompanyImportPayload(companies=[CompanyRecord(name=bad, source="test")])
    out = import_companies(payload, db_session)
    assert out["added"] == 0
    assert out["skipped"] == 1
    assert out["names"] == []


def test_import_skips_duplicate(db_session):
    name = "Contoso Foods LLC"
    ok, _ = is_valid_lead(name)
    assert ok is True

    p1 = CompanyImportPayload(companies=[CompanyRecord(name=name, source="test")])
    assert import_companies(p1, db_session)["added"] == 1

    p2 = CompanyImportPayload(companies=[CompanyRecord(name=name, source="test")])
    out = import_companies(p2, db_session)
    assert out["added"] == 0
    assert out["skipped"] == 1


def test_import_mixed_batch(db_session):
    payload = CompanyImportPayload(
        companies=[
            CompanyRecord(name="Beta Industries LLC"),
            CompanyRecord(name="Unlock the ROI"),
            CompanyRecord(name="Gamma Corp"),
        ]
    )
    out = import_companies(payload, db_session)
    assert out["added"] == 2
    assert out["skipped"] == 1
    assert set(out["names"]) == {"Beta Industries LLC", "Gamma Corp"}

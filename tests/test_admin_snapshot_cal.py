import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.admin_snapshot import _build_section
import app.models  # noqa: F401


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


def test_admin_snapshot_cal_section_builds(db_session):
    result = _build_section("cal", db_session)
    assert "summary" in result
    assert isinstance(result["summary"]["total"], int)
    assert "prospects" in result

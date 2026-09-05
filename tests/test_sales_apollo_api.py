import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import sales as sales_api
from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models
from app.models.crm import CrmAccount, Team, TeamMember
from app.models.sales_agent import SalesOpportunity


def test_opportunity_prospects_uses_apollo_with_account_context(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        user_id = uuid.uuid4()
        team_id = uuid.uuid4()
        account_id = uuid.uuid4()
        opportunity_id = uuid.uuid4()
        db.add(Team(id=team_id, name="Ready For Robots"))
        db.add(TeamMember(team_id=team_id, user_id=user_id, role="owner"))
        db.add(
            CrmAccount(
                id=account_id,
                team_id=team_id,
                name="Acme Logistics",
                website="https://www.acme.com",
                industry="logistics",
            )
        )
        db.add(
            SalesOpportunity(
                id=str(opportunity_id),
                team_id=str(team_id),
                crm_account_id=str(account_id),
                opportunity_type="crm",
                title="Acme Logistics",
                current_stage="qualified",
            )
        )
        db.commit()
        captured = {}

        class FakeClient:
            def search_people(self, **kwargs):
                captured.update(kwargs)
                return {"prospects": [{"name": "Jane Smith"}], "pagination": {"page": 1}, "request": kwargs}

        monkeypatch.setattr(sales_api, "ApolloProspectClient", lambda: FakeClient())

        result = sales_api.prospects_for_sales_opportunity(str(opportunity_id), db=db, user={"uid": str(user_id)})

        assert captured["organization_name"] == "Acme Logistics"
        assert captured["organization_domain"] == "acme.com"
        assert "VP Supply Chain" in captured["titles"]
        assert result["prospects"][0]["name"] == "Jane Smith"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

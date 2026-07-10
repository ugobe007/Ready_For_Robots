"""Special projects — admin CRUD + token-gated client portal."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.auth_deps import require_admin
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: {"uid": "admin", "email": "admin@example.com"}
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _create(client, **kw):
    payload = {"name": "NIMO Technology", **kw}
    res = client.post("/api/admin/special-projects", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_create_generates_slug_and_token(client):
    body = _create(client, robot_description="Tactile kitchen humanoid")
    assert body["slug"] == "nimo-technology"
    assert body["share_token"]
    assert body["portal_path"] == f"/p/{body['share_token']}"
    assert body["status"] == "discovery"


def test_slug_is_unique(client):
    a = _create(client)
    b = _create(client)
    assert a["slug"] != b["slug"]
    assert b["slug"].startswith("nimo-technology-")


def test_patch_metrics_status_and_pipeline(client):
    proj = _create(client)
    res = client.patch(
        f"/api/admin/special-projects/{proj['id']}",
        json={
            "status": "piloting",
            "metrics": {"demos_booked": 4, "pilots_signed": 1},
            "pipeline": {"targeted": 50, "contacted": 30, "demo": 4, "pilot_signed": 1},
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "piloting"
    assert body["metrics"]["demos_booked"] == 4
    assert body["pipeline"]["contacted"] == 30


def test_invalid_status_rejected(client):
    proj = _create(client)
    res = client.patch(f"/api/admin/special-projects/{proj['id']}", json={"status": "bogus"})
    assert res.status_code == 400


def test_add_update_and_list(client):
    proj = _create(client)
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "First demo booked", "body": "CloudKitchens demo Friday", "category": "milestone"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["update_count"] == 1
    assert body["updates"][0]["title"] == "First demo booked"
    assert body["updates"][0]["category"] == "milestone"


def test_invalid_update_category_rejected(client):
    proj = _create(client)
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "x", "category": "not-a-category"},
    )
    assert res.status_code == 400


def test_public_portal_returns_client_safe_view(client):
    proj = _create(client, summary="Tactile humanoid for kitchens")
    client.patch(
        f"/api/admin/special-projects/{proj['id']}",
        json={"metrics": {"demos_booked": 2}, "pipeline": {"targeted": 40, "contacted": 12, "demo": 2}},
    )
    client.post(
        f"/api/admin/special-projects/{proj['id']}/updates",
        json={"title": "Outreach live", "category": "outreach"},
    )

    # Public portal — no auth, by share token.
    res = client.get(f"/api/special-projects/portal/{proj['share_token']}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "NIMO Technology"
    assert body["summary"] == "Tactile humanoid for kitchens"
    assert body["metrics"]["demos_booked"] == 2
    # Funnel is ordered by the beta-motion stages.
    stages = [f["stage"] for f in body["funnel"]]
    assert stages == ["targeted", "contacted", "demo"]
    assert body["updates"][0]["title"] == "Outreach live"
    # Internal fields must NOT leak to the client.
    assert "share_token" not in body
    assert "slug" not in body
    assert "contact_email" not in body


def test_public_portal_unknown_token_404(client):
    res = client.get("/api/special-projects/portal/nope")
    assert res.status_code == 404


def test_rotate_token_invalidates_old(client):
    proj = _create(client)
    old = proj["share_token"]
    res = client.post(f"/api/admin/special-projects/{proj['id']}/rotate-token")
    assert res.status_code == 200
    new = res.json()["share_token"]
    assert new != old
    assert client.get(f"/api/special-projects/portal/{old}").status_code == 404
    assert client.get(f"/api/special-projects/portal/{new}").status_code == 200


# ── Target queue (Cal's review-first outreach pipeline) ─────────────────────────

def _add_target(client, project_id, **kw):
    payload = {"company": "CloudKitchens", "best_fit_task": "Bowl assembly", "sequence": "A", **kw}
    res = client.post(f"/api/admin/special-projects/{project_id}/targets", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_create_target_autogenerates_draft(client):
    proj = _create(client)
    t = _add_target(client, proj["id"], contact_name="Alex Rivera", signal="a new automation push")
    assert t["stage"] == "targeted"
    assert t["approved"] is False
    # Draft is composed from the sequence template with merge fields:
    # task personalizes the subject, company personalizes the body.
    assert "bowl assembly" in t["draft_subject"].lower()
    assert "CloudKitchens" in t["draft_body"]
    assert t["draft_body"].startswith("Hi Alex,")
    assert "no-cost pilot" in t["draft_body"]
    # Plain-language guardrails: no jargon, no "humanoid", no weak "Hi there,".
    assert "humanoid" not in t["draft_body"].lower()
    assert "not sim" not in t["draft_body"].lower()
    assert "Hi there" not in t["draft_body"]
    # Has an email guessed flag off since none was provided.
    assert t["contact_status"] == "none"
    assert t["can_send"] is False
    # Creating a target immediately rolls the funnel forward.
    listing = client.get(f"/api/admin/special-projects/{proj['id']}/targets").json()
    assert listing["pipeline"]["targeted"] == 1


def test_send_requires_approval_and_email(client):
    proj = _create(client)
    t = _add_target(client, proj["id"])
    # Not approved, no email → refused.
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send")
    assert res.status_code == 400
    # Approve but still no email → refused.
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/approve")
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send")
    assert res.status_code == 400


def test_send_moves_stage_and_records_activity(client, monkeypatch):
    sent = {}

    def fake_send(**kwargs):
        sent.update(kwargs)
        return {"id": "resend-123"}

    monkeypatch.setattr("app.services.cal_email_send.send_cal_email_via_resend", fake_send)

    proj = _create(client)
    t = _add_target(client, proj["id"], contact_email="ops@cloudkitchens.com")
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/approve")
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["stage"] == "contacted"
    assert body["sent_at"] is not None
    assert sent["to_email"] == "ops@cloudkitchens.com"

    # Funnel + KPIs recompute from real activity.
    listing = client.get(f"/api/admin/special-projects/{proj['id']}/targets").json()
    assert listing["pipeline"]["targeted"] == 1
    assert listing["pipeline"]["contacted"] == 1
    assert listing["metrics"]["contacted"] == 1

    # An outreach update lands on the timeline for the portal.
    portal = client.get(f"/api/special-projects/portal/{proj['share_token']}").json()
    assert any(u["category"] == "outreach" for u in portal["updates"])
    assert portal["accounts"][0]["company"] == "CloudKitchens"
    assert portal["accounts"][0]["contacted"] is True


def test_stage_advance_recomputes_funnel(client):
    proj = _create(client)
    t = _add_target(client, proj["id"])
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/stage",
        json={"stage": "demo"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["stage"] == "demo"
    listing = client.get(f"/api/admin/special-projects/{proj['id']}/targets").json()
    # Cumulative funnel: a demo-stage target counts for every earlier stage too.
    assert listing["pipeline"]["targeted"] == 1
    assert listing["pipeline"]["contacted"] == 1
    assert listing["pipeline"]["demo"] == 1
    assert listing["pipeline"]["pilot_signed"] == 0


def test_invalid_stage_rejected(client):
    proj = _create(client)
    t = _add_target(client, proj["id"])
    res = client.post(
        f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/stage",
        json={"stage": "bogus"},
    )
    assert res.status_code == 400


# ── Bulk sender review-first guarantee ──────────────────────────────────────────
# Regression guard: the batch sender must honor the SAME approval gate as the
# per-target /send endpoint. It must never send — nor auto-approve — a target
# that a human has not explicitly approved. (This is the gap that let a terse
# "ok" turn into 40 unapproved sends.)

class _FakeTarget:
    def __init__(self, approved, contact_email="ops@x.com", draft_subject="s",
                 draft_body="b", contact_status="verified", sent_at=None):
        self.approved = approved
        self.contact_email = contact_email
        self.draft_subject = draft_subject
        self.draft_body = draft_body
        self.contact_status = contact_status
        self.sent_at = sent_at


def test_bulk_sender_skips_unapproved_targets():
    from scripts.send_special_project import _eligible

    # Fully drafted + verified + has email, but NOT human-approved → ineligible.
    assert _eligible(_FakeTarget(approved="no"), scope="all") is False
    assert _eligible(_FakeTarget(approved=""), scope="all") is False
    assert _eligible(_FakeTarget(approved=None), scope="all") is False
    # Only an explicit human "yes" makes it eligible.
    assert _eligible(_FakeTarget(approved="yes"), scope="all") is True
    # Approved but already sent → not resent.
    assert _eligible(_FakeTarget(approved="yes", sent_at="2026-07-07"), scope="all") is False
    # Verified scope still filters guessed contacts even when approved.
    assert _eligible(_FakeTarget(approved="yes", contact_status="guessed"), scope="verified") is False
    assert _eligible(_FakeTarget(approved="yes", contact_status="guessed"), scope="all") is True


# ── Bulk send-approved endpoint (review-first) ──────────────────────────────────

def test_send_all_approved_only_sends_approved(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.services.cal_email_send.send_cal_email_via_resend",
        lambda **kw: calls.append(kw) or {"id": "r"},
    )
    proj = _create(client)
    # One approved+email, one with an email but NOT approved, one approved w/o email.
    a = _add_target(client, proj["id"], company="Approved Co", contact_email="a@x.com")
    _add_target(client, proj["id"], company="Unapproved Co", contact_email="b@x.com")
    c = _add_target(client, proj["id"], company="NoEmail Co")
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{a['id']}/approve")
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{c['id']}/approve")

    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/send-approved")
    assert res.status_code == 200, res.text
    body = res.json()
    # Only the approved-with-email target is eligible + sent.
    assert body["eligible"] == 1
    assert body["sent"] == 1
    assert len(calls) == 1
    assert calls[0]["to_email"] == "a@x.com"

    # Re-running sends nothing (already sent → not eligible again).
    res2 = client.post(f"/api/admin/special-projects/{proj['id']}/targets/send-approved")
    assert res2.json()["sent"] == 0


# ── Follow-up (T2) — review-first second touch ──────────────────────────────────

def _send_first(client, project_id, monkeypatch, **kw):
    monkeypatch.setattr(
        "app.services.cal_email_send.send_cal_email_via_resend", lambda **k: {"id": "r"}
    )
    t = _add_target(client, project_id, contact_email="ops@x.com", **kw)
    client.post(f"/api/admin/special-projects/{project_id}/targets/{t['id']}/approve")
    client.post(f"/api/admin/special-projects/{project_id}/targets/{t['id']}/send")
    return t


def test_generate_followups_only_for_contacted(client, monkeypatch):
    proj = _create(client)
    contacted = _send_first(client, proj["id"], monkeypatch, company="Contacted Co")
    # A never-contacted target must NOT get a follow-up draft.
    _add_target(client, proj["id"], company="Fresh Co", contact_email="f@x.com")

    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/generate-followups")
    assert res.status_code == 200, res.text
    assert res.json()["generated"] == 1

    listing = client.get(f"/api/admin/special-projects/{proj['id']}/targets").json()
    by_company = {t["company"]: t for t in listing["targets"]}
    assert by_company["Contacted Co"]["followup_subject"]
    assert by_company["Contacted Co"]["followup_approved"] is False
    assert by_company["Fresh Co"]["followup_subject"] in (None, "")


def test_followup_send_requires_approval(client, monkeypatch):
    proj = _create(client)
    t = _send_first(client, proj["id"], monkeypatch, company="Contacted Co")
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/generate-followups")

    # Not approved → refused.
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send-followup")
    assert res.status_code == 400

    # Approve then send.
    sent = []
    monkeypatch.setattr(
        "app.services.cal_email_send.send_cal_email_via_resend",
        lambda **kw: sent.append(kw) or {"id": "r"},
    )
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/approve-followup")
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send-followup")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["followup_sent_at"] is not None
    assert len(sent) == 1
    # The follow-up carries the T2 subject, not the T1 subject.
    assert sent[0]["subject"] != body["draft_subject"]

    # Cannot double-send the follow-up.
    res2 = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send-followup")
    assert res2.status_code == 400


def test_followup_cannot_send_before_first_touch(client):
    # A target that was never contacted has no valid follow-up path.
    proj = _create(client)
    t = _add_target(client, proj["id"], contact_email="x@x.com")
    client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/approve-followup")
    res = client.post(f"/api/admin/special-projects/{proj['id']}/targets/{t['id']}/send-followup")
    assert res.status_code == 400

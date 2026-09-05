"""Tests for LinkedIn OAuth helpers."""
import os

from app.services.linkedin_oauth import organization_id, organization_urn


def test_default_organization():
    os.environ.pop("LINKEDIN_ORGANIZATION_ID", None)
    os.environ["LINKEDIN_POST_MODE"] = "member"
    assert organization_id() == "114404417"
    assert organization_urn() == "urn:li:organization:114404417"


def test_member_mode_default_scopes():
    os.environ["LINKEDIN_POST_MODE"] = "member"
    from app.services import linkedin_oauth as mod

    assert mod.post_mode() == "member"
    assert "w_member_social" in mod.oauth_scopes()
    assert "w_organization_social" not in mod.oauth_scopes()

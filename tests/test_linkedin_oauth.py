"""Tests for LinkedIn OAuth helpers."""
import os

from app.services.linkedin_oauth import organization_id, organization_urn


def test_default_organization():
    os.environ.pop("LINKEDIN_ORGANIZATION_ID", None)
    assert organization_id() == "114404417"
    assert organization_urn() == "urn:li:organization:114404417"

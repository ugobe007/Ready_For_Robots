"""Vercel Git previews must be able to call Fly without a per-branch CORS edit."""
from app.main import _is_allowed_cors_origin


def test_vercel_git_preview_origin_is_allowed():
    assert _is_allowed_cors_origin(
        "https://ready-for-robots-git-cursor-n-dda16d-ugobe07-gmailcoms-projects.vercel.app"
    )


def test_unrelated_vercel_app_is_not_allowed():
    assert _is_allowed_cors_origin("https://some-other-app.vercel.app") is False


def test_production_origin_is_allowed():
    assert _is_allowed_cors_origin("https://readyforrobots.com")

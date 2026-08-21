"""Bot-challenge pages must not become robot identity; archive URLs unwrap."""
from __future__ import annotations

from app.services.robot_profile_cache import _profile_is_cacheable
from app.services.robot_understanding_v1.fetch import (
    is_bot_challenge,
    unwrap_archive_url,
)


def test_unwrap_archive_url_returns_manufacturer_host():
    wrapped = (
        "https://web.archive.org/web/20260514191727/"
        "https://richtechrobotics.com/adam"
    )
    assert unwrap_archive_url(wrapped) == "https://richtechrobotics.com/adam"
    relative = "/web/20260514191727/https://www.richtechrobotics.com/matradee-l"
    assert unwrap_archive_url(relative) == "https://www.richtechrobotics.com/matradee-l"
    live = "https://www.richtechrobotics.com/"
    assert unwrap_archive_url(live) == live


def test_vercel_checkpoint_is_a_bot_challenge():
    html = "<html><title>Vercel Security Checkpoint</title><body>Enable JavaScript to continue</body></html>"
    assert is_bot_challenge(
        status_code=429,
        title="Vercel Security Checkpoint",
        html=html,
        headers={"x-vercel-mitigated": "challenge"},
    )
    assert is_bot_challenge(
        status_code=200,
        title="Vercel Security Checkpoint",
        html=html,
        headers={},
    )
    assert not is_bot_challenge(
        status_code=200,
        title="AI-driven robotics - Richtech Robotics",
        html="<html><body>ADAM serves cocktails</body></html>",
        headers={},
    )


def test_hollow_challenge_profiles_are_not_cached():
    assert not _profile_is_cacheable(
        {
            "company": {"name": "Richtech Robotics", "primary_domain": "richtechrobotics.com"},
            "products": [],
            "sources": [],
            "selected_product": None,
            "notes": ["Bot challenge from manufacturer host (HTTP 429)"],
        }
    )
    assert _profile_is_cacheable(
        {
            "company": {"name": "Richtech Robotics"},
            "products": [{"name": "ADAM"}],
            "sources": [],
            "selected_product": None,
            "notes": [],
        }
    )


def test_fetch_page_uses_archive_when_live_host_challenges(monkeypatch):
    from types import SimpleNamespace

    from app.services.robot_understanding_v1 import fetch as F

    live_html = "<html><title>Vercel Security Checkpoint</title><body>Enable JavaScript to continue</body></html>"
    archive_html = """
    <html><title>AI-driven robotics - Richtech Robotics</title>
    <body>
      <a href="/adam">ADAM</a>
      <p>ADAM serves cocktails at NVIDIA HQ.</p>
    </body></html>
    """

    def fake_get(url: str, *, timeout):
        if "web.archive.org" in url:
            return SimpleNamespace(
                url="https://web.archive.org/web/20260514191727/https://richtechrobotics.com/",
                status_code=200,
                headers={"Content-Type": "text/html"},
                content=archive_html.encode(),
                text=archive_html,
            )
        return SimpleNamespace(
            url="https://richtechrobotics.com/",
            status_code=429,
            headers={"Content-Type": "text/html", "x-vercel-mitigated": "challenge"},
            content=live_html.encode(),
            text=live_html,
        )

    monkeypatch.setattr(F, "_get", fake_get)
    monkeypatch.setattr(F, "assert_public_http_url", lambda url: url)
    page = F.fetch_page("https://richtechrobotics.com/")
    assert page.fetch_degraded is False
    assert "ADAM serves" in page.text
    assert any("adam" in url.lower() for url, _ in page.links)
    assert any("archive" in n.lower() for n in page.fetch_notes)


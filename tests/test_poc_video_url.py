"""Allowlisted HTTPS PoC video URLs — no file upload, empty does not block."""
from __future__ import annotations

import pytest

from app.services.poc_video_url import (
    POC_VIDEO_BAD_HOST,
    POC_VIDEO_BAD_SCHEME,
    normalize_poc_video_url,
    poc_video_embed_url,
    poc_video_kind,
)


def test_empty_url_is_none():
    assert normalize_poc_video_url("") is None
    assert normalize_poc_video_url("   ") is None
    assert normalize_poc_video_url(None) is None
    assert poc_video_embed_url("") is None


@pytest.mark.parametrize(
    "raw,kind,embed_contains",
    [
        (
            "https://www.loom.com/share/abcd1234efgh5678",
            "loom",
            "loom.com/embed/abcd1234efgh5678",
        ),
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube",
            "youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        (
            "https://youtu.be/dQw4w9WgXcQ",
            "youtube",
            "youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        (
            "https://vimeo.com/123456789",
            "vimeo",
            "player.vimeo.com/video/123456789",
        ),
    ],
)
def test_allowlisted_embed_hosts(raw, kind, embed_contains):
    cleaned = normalize_poc_video_url(raw)
    assert cleaned and cleaned.startswith("https://")
    assert poc_video_kind(cleaned) == kind
    embed = poc_video_embed_url(cleaned)
    assert embed and embed_contains in embed
    assert embed.startswith("https://")


def test_google_drive_is_link_out_not_embed():
    raw = "https://drive.google.com/file/d/abcDEF123/view"
    cleaned = normalize_poc_video_url(raw)
    assert cleaned.startswith("https://drive.google.com/")
    assert poc_video_kind(cleaned) == "drive"
    assert poc_video_embed_url(cleaned) is None


def test_http_and_unknown_host_rejected_without_echoing_url():
    sneaky = "http://www.loom.com/share/abcd1234efgh5678"
    with pytest.raises(ValueError) as http_err:
        normalize_poc_video_url(sneaky)
    assert POC_VIDEO_BAD_SCHEME in str(http_err.value)
    assert sneaky not in str(http_err.value)
    assert "loom.com/share" not in str(http_err.value)

    junk = "https://evil.example/watch?v=dQw4w9WgXcQ"
    with pytest.raises(ValueError) as host_err:
        normalize_poc_video_url(junk)
    assert POC_VIDEO_BAD_HOST in str(host_err.value)
    assert junk not in str(host_err.value)
    assert "evil.example" not in str(host_err.value)


def test_rejects_credentials_and_non_https_schemes():
    with pytest.raises(ValueError, match="HTTPS"):
        normalize_poc_video_url("javascript:alert(1)")
    with pytest.raises(ValueError, match="HTTPS"):
        normalize_poc_video_url("https://user:pass@www.loom.com/share/abcd1234")

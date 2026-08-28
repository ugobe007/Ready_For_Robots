"""Allowlisted HTTPS video résumé URLs for Jobs CRM apply.

Paste Loom / YouTube / Vimeo (embed) or Google Drive (link-out).
No video file upload. Empty is valid — PoC stays skippable (F11).
Error strings must not echo the pasted URL.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

POC_VIDEO_MAX_LEN = 2000

POC_VIDEO_BAD_SCHEME = (
    "Paste an HTTPS Loom, YouTube, Vimeo, or Google Drive link. "
    "Empty is fine — this does not block apply."
)
POC_VIDEO_BAD_HOST = (
    "That host is not allowed. Use Loom, YouTube, Vimeo, or Google Drive."
)
POC_VIDEO_TOO_LONG = "Video URL is too long."

_EMBED_KINDS = ("loom", "youtube", "vimeo")
_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_LOOM_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_VIMEO_ID = re.compile(r"^(\d{5,12})$")


def _bare_host(host: str) -> str:
    h = (host or "").lower().rstrip(".")
    if h.startswith("www."):
        h = h[4:]
    return h


def _host_matches(host: str, suffixes: tuple[str, ...]) -> bool:
    h = _bare_host(host)
    for suffix in suffixes:
        if h == suffix or h.endswith("." + suffix):
            return True
    return False


def classify_poc_video_host(host: str) -> str | None:
    if _host_matches(host, ("youtu.be", "youtube.com")):
        return "youtube"
    if _host_matches(host, ("loom.com",)):
        return "loom"
    if _host_matches(host, ("vimeo.com",)):
        return "vimeo"
    if _host_matches(host, ("drive.google.com",)):
        return "drive"
    return None


def normalize_poc_video_url(raw: str | None) -> str | None:
    """Return a cleaned HTTPS URL, or None when empty.

    Raises ValueError on a non-empty invalid value. Messages omit the URL.
    """
    text = (raw or "").strip()
    if not text:
        return None
    if len(text) > POC_VIDEO_MAX_LEN:
        raise ValueError(POC_VIDEO_TOO_LONG)
    parsed = urlparse(text)
    if parsed.scheme.lower() != "https":
        raise ValueError(POC_VIDEO_BAD_SCHEME)
    if parsed.username or parsed.password:
        raise ValueError(POC_VIDEO_BAD_SCHEME)
    host = parsed.hostname or ""
    if not classify_poc_video_host(host):
        raise ValueError(POC_VIDEO_BAD_HOST)
    cleaned = parsed._replace(netloc=host.lower(), fragment="").geturl()
    return cleaned


def poc_video_kind(url: str | None) -> str | None:
    text = (url or "").strip()
    if not text:
        return None
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    if parsed.scheme.lower() != "https":
        return None
    return classify_poc_video_host(parsed.hostname or "")


def poc_video_embed_url(url: str | None) -> str | None:
    """Safe iframe src for Loom / YouTube / Vimeo. Drive is link-out only."""
    text = (url or "").strip()
    if not text:
        return None
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    if parsed.scheme.lower() != "https":
        return None
    kind = classify_poc_video_host(parsed.hostname or "")
    if kind not in _EMBED_KINDS:
        return None
    host = _bare_host(parsed.hostname or "")
    parts = [p for p in (parsed.path or "").split("/") if p]
    query = parse_qs(parsed.query or "")

    if kind == "youtube":
        vid = ""
        if host == "youtu.be" and parts:
            vid = parts[0]
        elif "v" in query and query["v"]:
            vid = query["v"][0]
        elif parts and parts[0] in {"embed", "shorts", "v"} and len(parts) > 1:
            vid = parts[1]
        vid = (vid or "").split("?")[0].split("&")[0]
        if not _YOUTUBE_ID.match(vid):
            return None
        return f"https://www.youtube-nocookie.com/embed/{vid}"

    if kind == "loom":
        share = ""
        if parts and parts[0] in {"share", "embed"} and len(parts) > 1:
            share = parts[1]
        elif parts:
            share = parts[-1]
        share = (share or "").split("?")[0]
        if not _LOOM_ID.match(share):
            return None
        return f"https://www.loom.com/embed/{share}"

    if kind == "vimeo":
        vid = ""
        if parts and parts[0] == "video" and len(parts) > 1:
            vid = parts[1]
        else:
            for part in reversed(parts):
                if _VIMEO_ID.match(part):
                    vid = part
                    break
        if not _VIMEO_ID.match(vid or ""):
            return None
        return f"https://player.vimeo.com/video/{vid}"

    return None

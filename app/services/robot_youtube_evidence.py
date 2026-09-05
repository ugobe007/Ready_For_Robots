"""Find a public YouTube watch URL for a named robot SKU.

Fails empty rather than attaching the wrong robot's video.
Uses YouTube Data API when YOUTUBE_API_KEY is set. Otherwise returns a
documented search URL and may scrape the first result only when the title
clearly names the same robot.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.services.poc_video_url import normalize_poc_video_url

YOUTUBE_WATCH = "https://www.youtube.com/watch?v={vid}"
YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query={q}"
YOUTUBE_SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_UA = "ReadyForRobots/jobs-apply (+https://readyforrobots.com)"
_TIMEOUT = 8

VIDEO_EMPTY_NOTE = (
    "No public YouTube clip of this robot turned up. "
    "We left the video empty rather than guess."
)
VIDEO_KEY_MISSING_NOTE = (
    "No YouTube API key on this host. Search is open in YouTube. "
    "We did not pick a video unless the first result clearly named this robot."
)


def youtube_search_query(company: str | None, sku: str | None, robot: str | None) -> str:
    parts: list[str] = []
    for raw in (company, sku or robot):
        text = re.sub(r"\s+", " ", (raw or "").strip())
        if text and text.lower() not in {"your robot", "this robot"}:
            if text.lower() not in [p.lower() for p in parts]:
                parts.append(text)
    if not parts:
        return ""
    return " ".join(parts)


def youtube_search_url(company: str | None, sku: str | None, robot: str | None) -> str:
    q = youtube_search_query(company, sku, robot)
    if not q:
        return ""
    return YOUTUBE_SEARCH.format(q=urllib.parse.quote_plus(q))


def _sku_tokens(sku: str | None) -> list[str]:
    text = (sku or "").strip().lower()
    if not text:
        return []
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if len(t) >= 2]


def title_names_robot(title: str, *, sku: str | None, company: str | None) -> bool:
    """True only when the title clearly names this SKU. Company alone is not enough."""
    hay = (title or "").lower()
    if not hay:
        return False
    compact = re.sub(r"[^a-z0-9]+", "", hay)
    sku_raw = (sku or "").strip()
    if sku_raw:
        sku_compact = re.sub(r"[^a-z0-9]+", "", sku_raw.lower())
        if len(sku_compact) >= 2 and sku_compact in compact:
            return True
        tokens = _sku_tokens(sku_raw)
        if tokens and all(tok in hay for tok in tokens):
            return True
        return False
    return False


def _watch_url(video_id: str) -> str | None:
    vid = (video_id or "").strip()
    if not _VIDEO_ID.match(vid):
        return None
    try:
        return normalize_poc_video_url(YOUTUBE_WATCH.format(vid=vid))
    except ValueError:
        return None


def _http_get(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read(1_500_000)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def _pick_from_items(
    items: list[dict[str, Any]],
    *,
    sku: str | None,
    company: str | None,
) -> dict[str, Any] | None:
    for item in items:
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        title = str(snippet.get("title") or item.get("title") or "")
        if not title_names_robot(title, sku=sku, company=company):
            continue
        vid = ""
        ident = item.get("id")
        if isinstance(ident, dict):
            vid = str(ident.get("videoId") or "")
        elif isinstance(ident, str):
            vid = ident
        if not vid:
            vid = str(item.get("videoId") or item.get("id") or "")
        url = _watch_url(vid)
        if not url:
            continue
        desc = str(snippet.get("description") or item.get("description") or "").strip() or None
        return {
            "video_url": url,
            "clip_description": (desc[:280] if desc else title.strip() or None),
            "title": title,
        }
    return None


def _search_data_api(query: str, *, sku: str | None, company: str | None) -> dict[str, Any] | None:
    key = (os.getenv("YOUTUBE_API_KEY") or "").strip()
    if not key or not query:
        return None
    params = urllib.parse.urlencode(
        {
            "part": "snippet",
            "type": "video",
            "maxResults": "8",
            "q": query,
            "key": key,
        }
    )
    body = _http_get(f"{YOUTUBE_SEARCH_API}?{params}")
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None
    return _pick_from_items(items, sku=sku, company=company)


def _scrape_search_html(query: str, *, sku: str | None, company: str | None) -> dict[str, Any] | None:
    if not query:
        return None
    html = _http_get(YOUTUBE_SEARCH.format(q=urllib.parse.quote_plus(query)))
    if not html:
        return None
    blob = html
    marker = "ytInitialData"
    start = html.find(marker)
    if start >= 0:
        brace = html.find("{", start)
        if brace >= 0:
            blob = html[brace : brace + 400_000]
    items: list[dict[str, Any]] = []
    for match in re.finditer(
        r'"videoId":"([A-Za-z0-9_-]{11})".{0,400}?"title":\{"runs":\[\{"text":"(.*?)"\}',
        blob,
        flags=re.DOTALL,
    ):
        items.append(
            {
                "id": {"videoId": match.group(1)},
                "snippet": {"title": match.group(2).encode("utf-8").decode("unicode_escape", errors="replace")},
            }
        )
        if len(items) >= 8:
            break
    if not items:
        ids = re.findall(r"watch\?v=([A-Za-z0-9_-]{11})", html)
        titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"\}', html)
        for vid, title in zip(ids, titles):
            items.append({"id": {"videoId": vid}, "snippet": {"title": title}})
            if len(items) >= 8:
                break
    return _pick_from_items(items, sku=sku, company=company)


def find_robot_youtube_evidence(
    *,
    company: str | None = None,
    sku: str | None = None,
    robot: str | None = None,
) -> dict[str, Any]:
    """Return a watch URL only when a public video clearly names this robot."""
    sku_name = (sku or robot or "").strip() or None
    query = youtube_search_query(company, sku_name, robot)
    search = youtube_search_url(company, sku_name, robot)
    empty = {
        "video_url": None,
        "video_search_url": search,
        "video_note": VIDEO_EMPTY_NOTE,
        "clip_description": None,
        "query": query,
        "source": "none",
    }
    if not query or not sku_name:
        return empty

    hit = _search_data_api(query, sku=sku_name, company=company)
    source = "youtube_data_api"
    if not hit:
        hit = _scrape_search_html(query, sku=sku_name, company=company)
        source = "youtube_search_html"
    if not hit:
        note = VIDEO_EMPTY_NOTE
        if not (os.getenv("YOUTUBE_API_KEY") or "").strip():
            note = f"{VIDEO_KEY_MISSING_NOTE} {VIDEO_EMPTY_NOTE}"
        return {**empty, "video_note": note, "source": "search_only"}

    return {
        "video_url": hit["video_url"],
        "video_search_url": search,
        "video_note": f"Public YouTube clip that names {sku_name}.",
        "clip_description": hit.get("clip_description"),
        "query": query,
        "source": source,
    }

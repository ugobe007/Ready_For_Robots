"""
Normalize signal text for classification (strip RSS/HTML, keep anchor headlines).
"""
from __future__ import annotations

import html
import re

_ANCHOR_TEXT_RE = re.compile(r"<a[^>]*>([^<]+)</a>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_signal_html(text: str) -> str:
    """Remove RSS/HTML markup; prefer visible anchor text when present."""
    if not text or not str(text).strip():
        return ""
    t = str(text)
    anchors = _ANCHOR_TEXT_RE.findall(t)
    if anchors:
        t = " ".join(a.strip() for a in anchors if a.strip()) or t
    t = _TAG_RE.sub(" ", t)
    t = html.unescape(t)
    t = re.sub(r"https?://\S+", " ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t

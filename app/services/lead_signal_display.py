"""
Sales-facing text derived from ``signals.signal_text``.

Ingestion often stores long snippets, HTML, or LLM/scraper scaffolding (e.g. ``[code]``,
fenced blocks, meta lines). After historical cleanup, ``signals.ingestion_raw_text`` may
hold the pre-normalization body; the public API exposes that as ``raw_text`` when set.
``display_text`` and sentence helpers apply a short cap for cards; use
``normalize_signal_text_for_storage`` for full-body DB cleanup (see ``scripts/cleanup_signal_text.py``).
"""
from __future__ import annotations

import html
import re
from typing import Any, Optional

_BRACKET_SCRAP = re.compile(
    r"\[(?:code|explanation|explain|reason|rationale|notes?|summary|outputs?|results?|"
    r"source|context|snippets?|json|analysis|details?|thinking|translation|metadata|"
    r"language|prompt|instruction|steps?|fields?|values?|types?|labels?|entities?)\]",
    re.I,
)
_LINE_META = re.compile(
    r"^\s*(?:confidence|rationale|explanation|reasoning|analysis|outputs?|"
    r"notes?|sources?|metadata|json)\s*[:#\-]?\s*",
    re.I,
)
_URL_ONLY = re.compile(r"^https?://\S+$", re.I)


def _strip_fenced_code(t: str) -> str:
    return re.sub(r"```[\s\S]*?```", " ", t)


def _strip_inline_code(t: str) -> str:
    def repl(m):
        inner = m.group(1)
        if len(inner) > 80:
            return " "
        return inner

    return re.sub(r"`([^`]+)`", repl, t)


def strip_extraction_artifacts(text: Optional[str]) -> str:
    if not text:
        return ""
    t = html.unescape(str(text)).replace("\xa0", " ")
    # Prefer visible anchor text over raw Google News RSS markup.
    anchors = re.findall(r"<a[^>]*>([^<]+)</a>", t, flags=re.I)
    if anchors:
        joined = " ".join(a.strip() for a in anchors if a.strip())
        if len(joined) >= 24:
            t = joined
    t = re.sub(r"<\s*font[^>]*>([^<]*)</\s*font\s*>", r"\1", t, flags=re.I)
    t = re.sub(r"<\s*a\s*href\s*=\s*['\"][^'\"]*['\"][^>]*>(.*?)</a>", r"\1", t, flags=re.I | re.S)
    t = re.sub(r"<\s*ahref\s*=\s*['\"][^'\"]*['\"][^>]*>(.*?)</a>", r"\1", t, flags=re.I | re.S)
    t = re.sub(r"\bsource_url\s*[:=]?\s*", " ", t, flags=re.I)
    t = re.sub(r"\b(?:a?href|target|rel|class|style|title)\s*=\s*['\"][^'\"]*['\"]", " ", t, flags=re.I)
    t = re.sub(r"\b(?:a?href)\s*=\s*https?://\S+", " ", t, flags=re.I)
    t = re.sub(r"https?://\S+", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"#6f6f6f", " ", t, flags=re.I)
    t = re.sub(r"\b(?:ca|cc|ved|usg)=[^\s\"'<>]+", " ", t, flags=re.I)
    t = re.sub(r"(^|\s)>+", " ", t)
    t = _strip_fenced_code(t)
    t = _BRACKET_SCRAP.sub(" ", t)
    t = _strip_inline_code(t)
    lines_out: list[str] = []
    for line in t.splitlines():
        ln = line.strip()
        if not ln:
            continue
        if _LINE_META.match(ln):
            continue
        lines_out.append(line)
    t = " ".join(lines_out)
    t = re.sub(r"\*{1,2}([^*]{1,240})\*{1,2}", r"\1", t)
    t = " ".join(t.split())
    return t.strip()


def pick_primary_sentence(text: Optional[str], *, max_chars: int = 220) -> str:
    """
    One sentence tuned for rep skim: strip scaffolding, skip generic lead-ins,
    prefer the first substantive clause.
    """
    t = strip_extraction_artifacts(text)
    if not t:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", t)
    skip_prefixes = (
        "based on",
        "according to",
        "this article",
        "the following",
        "here is",
        "summary:",
        "in summary",
        "overall,",
        "note that",
        "the article",
        "the press release",
    )
    substantive: list[str] = []
    for p in parts:
        piece = p.strip()
        if len(piece) < 22:
            continue
        low = piece.lower()
        if any(low.startswith(s) for s in skip_prefixes):
            continue
        if piece.count("http") >= 1 and len(piece) < 90:
            continue
        if _URL_ONLY.match(piece):
            continue
        substantive.append(piece)
    chosen = substantive[0] if substantive else parts[0].strip() if parts else t
    if len(chosen) > max_chars:
        cut = chosen[: max_chars - 1].rsplit(" ", 1)[0]
        chosen = (cut or chosen[:max_chars]).rstrip(",; ") + "…"
    return chosen


def normalize_signal_text_for_storage(raw: Optional[str], *, max_chars: int = 8000) -> str:
    """
    Full-body cleanup for persisting on ``signals.signal_text`` (not the short card cap).

    Strips the same scaffolding as ``strip_extraction_artifacts`` then applies a hard
    length cap so VARCHAR/Text columns stay bounded on older databases.
    """
    t = strip_extraction_artifacts(raw)
    if not t:
        return ""
    if len(t) <= max_chars:
        return t
    cut = t[: max_chars - 1].rsplit(" ", 1)[0]
    return (cut or t[:max_chars]).rstrip(",; ") + "…"


def format_signal_for_sales(raw: Optional[str], *, max_chars: int = 360) -> str:
    """One complete sales-facing sentence; avoids mid-clause scraper fragments."""
    from app.services.lead_sales_copy import is_low_quality_sales_text

    sentence = pick_primary_sentence(raw, max_chars=max_chars)
    if sentence and not is_low_quality_sales_text(sentence):
        return sentence

    t = strip_extraction_artifacts(raw)
    if not t or is_low_quality_sales_text(t):
        return ""
    if len(t) <= max_chars:
        return t
    cut = t[: max_chars - 1].rsplit(" ", 1)[0]
    return (cut or t[:max_chars]).rstrip(",; ") + "…"


def core_need_from_top_signal(top: Any) -> str:
    """``top`` is a SQLAlchemy ``Signal`` (or any object with ``signal_text``)."""
    if top is None:
        return ""
    raw = getattr(top, "signal_text", None) or ""
    return pick_primary_sentence(raw, max_chars=200)

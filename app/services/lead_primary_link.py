"""
Resolve the best external URL for a sales lead (company site vs signal evidence).
Drive follow-up policy when identity cannot be anchored to a URL.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

# Below this overall score, a lead with no site and no evidence URL is a removal candidate.
REVIEW_FOR_REMOVAL_SCORE_MAX = 22.0
# Above this, keep even without a resolvable URL (strong intent elsewhere).
KEEP_WITHOUT_URL_SCORE_MIN = 38.0


_SEED_PLACEHOLDER = re.compile(r"^seed(_v\d+)?$", re.I)


def _looks_like_http_url(s: Optional[str]) -> bool:
    if not s or not isinstance(s, str):
        return False
    u = s.strip()
    if len(u) < 12:
        return False
    if not u.startswith(("http://", "https://")):
        return False
    try:
        from urllib.parse import urlparse

        p = urlparse(u)
        return bool(p.netloc and "." in p.netloc)
    except Exception:
        return False


def _is_placeholder_source(url: Optional[str]) -> bool:
    if not url or not str(url).strip():
        return True
    u = str(url).strip()
    if _SEED_PLACEHOLDER.match(u):
        return True
    if u.lower() in ("unknown", "n/a", "none"):
        return True
    return False


def _signal_source_url(sig: Any) -> Optional[str]:
    if sig is None:
        return None
    if isinstance(sig, dict):
        return sig.get("source_url")
    return getattr(sig, "source_url", None)


def first_evidence_http_url(signals: Optional[Iterable[Any]]) -> Optional[str]:
    """First http(s) source_url on a signal row (news / PR), excluding seed placeholders."""
    if not signals:
        return None
    for sig in signals:
        raw = _signal_source_url(sig)
        if _is_placeholder_source(raw):
            continue
        if _looks_like_http_url(raw):
            return str(raw).strip()
    return None


def enrich_lead_link_fields(
    *,
    website: Optional[str],
    signals: Optional[Iterable[Any]],
    overall_score: float = 0.0,
    signal_count: Optional[int] = None,
    llm_resolved_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Returns keys for API JSON:
      primary_link_url, primary_link_kind ('website'|'evidence'|'inferred_openai'|None),
      identity_resolution, needs_website_inference, suggested_pipeline_action

    ``llm_resolved_url``: optional https homepage from OpenAI batch resolve
    (``COMPANY_URL_OPENAI_RESOLVE``); used only when website and evidence are absent.
    """
    sigs = list(signals) if signals is not None else []
    n_sig = signal_count if signal_count is not None else len(sigs)
    score = float(overall_score or 0.0)

    site_ok = _looks_like_http_url(website)
    evidence = None if site_ok else first_evidence_http_url(sigs)
    llm_u = (llm_resolved_url or "").strip()
    llm_ok = _looks_like_http_url(llm_u) if not site_ok and not evidence else False

    if site_ok:
        url = str(website).strip()
        kind = "website"
        resolution = "website"
        needs_inf = False
    elif evidence:
        url = evidence
        kind = "evidence"
        resolution = "evidence"
        needs_inf = False
    elif llm_ok:
        url = llm_u
        kind = "inferred_openai"
        resolution = "inferred_openai"
        needs_inf = False
    else:
        url = None
        kind = None
        resolution = "unresolved"
        needs_inf = True

    # keep | infer_website | review_for_removal (never auto-delete — ops decide)
    if resolution != "unresolved":
        action = "keep"
    elif score >= KEEP_WITHOUT_URL_SCORE_MIN or n_sig >= 3:
        action = "infer_website"
    elif n_sig >= 1 and score >= 15.0:
        action = "infer_website"
    elif score <= REVIEW_FOR_REMOVAL_SCORE_MAX and n_sig <= 1:
        action = "review_for_removal"
    else:
        action = "infer_website"

    return {
        "primary_link_url": url,
        "primary_link_kind": kind,
        "identity_resolution": resolution,
        "needs_website_inference": needs_inf,
        "suggested_pipeline_action": action,
    }

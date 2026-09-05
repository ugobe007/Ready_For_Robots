"""
Best-effort company website discovery (admin / batch jobs).
Uses DuckDuckGo Instant Answer JSON — no API key; rate-limit callers.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Optional

from app.services.lead_primary_link import _looks_like_http_url
from app.services.company_domain import is_trusted_outreach_domain, normalize_website_domain

logger = logging.getLogger(__name__)

DDG_API = "https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"


def try_duckduckgo_company_website(company_name: str, *, timeout: float = 10.0) -> Optional[str]:
    """
    Return a canonical-looking http(s) URL from DDG instant answers, or None.
    Not deterministic; use only as enrichment hint + manual verification.
    """
    name = (company_name or "").strip()
    if len(name) < 2:
        return None
    q = urllib.parse.quote(f"{name} official website")
    url = DDG_API.format(q=q)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ReadyForRobots/1.0 (website inference)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.debug("DDG lookup failed for %r: %s", name, e)
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    candidates: list[str] = []

    au = data.get("AbstractURL") or data.get("OfficialWebsite")
    if isinstance(au, str) and _looks_like_http_url(au):
        candidates.append(au.strip())

    def walk_topics(topics):
        if not topics:
            return
        for t in topics:
            if isinstance(t, dict):
                fu = t.get("FirstURL")
                if isinstance(fu, str) and _looks_like_http_url(fu):
                    candidates.append(fu.strip())
                nested = t.get("Topics")
                if nested:
                    walk_topics(nested)

    walk_topics(data.get("RelatedTopics") or [])

    # Prefer non-aggregator first party domains
    bad_sub = ("facebook.com", "linkedin.com", "twitter.com", "instagram.com", "wikipedia.org", "crunchbase.com")
    for c in candidates:
        low = c.lower()
        if not any(b in low for b in bad_sub):
            dom = normalize_website_domain(c)
            if dom and is_trusted_outreach_domain(dom):
                return c
    for c in candidates:
        dom = normalize_website_domain(c)
        if dom and is_trusted_outreach_domain(dom):
            return c
    return None


def sleep_between_lookups(seconds: float = 0.75) -> None:
    time.sleep(seconds)

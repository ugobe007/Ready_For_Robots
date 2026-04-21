"""
Batch-resolve likely official homepages for company names via OpenAI.

Used when real `website` and signal `source_url` evidence are missing, so the UI
can prefer a model-suggested https URL over a generic web search.

Enable with ``COMPANY_URL_OPENAI_RESOLVE=1`` and ``OPENAI_API_KEY`` (same as other
OpenAI features). Model: ``COMPANY_URL_OPENAI_MODEL`` (default ``gpt-4o-mini``).

Responses are cached in-process (TTL ``COMPANY_URL_OPENAI_CACHE_SEC``, default 86400)
to avoid repeated calls for the same name across requests.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, str]] = {}


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid %s=%r — using default %s", name, raw, default)
        return default


_TTL_SEC = _env_float("COMPANY_URL_OPENAI_CACHE_SEC", 86400.0)


def openai_url_resolve_enabled() -> bool:
    return os.getenv("COMPANY_URL_OPENAI_RESOLVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _cache_get_url(key: str) -> Optional[str]:
    """Return cached https URL if present and fresh; otherwise None."""
    now = time.monotonic()
    ent = _CACHE.get(key)
    if not ent:
        return None
    ts, val = ent
    if now - ts > _TTL_SEC:
        del _CACHE[key]
        return None
    return val


def _cache_set_url(key: str, val: str) -> None:
    _CACHE[key] = (time.monotonic(), val)


def _looks_ok_https(u: str) -> bool:
    u = (u or "").strip()
    if len(u) < 12 or not u.startswith("https://"):
        return False
    try:
        from urllib.parse import urlparse

        p = urlparse(u)
        return bool(p.netloc and "." in p.netloc)
    except Exception:
        return False


def _batch_openai_urls(names: list[str]) -> dict[str, Optional[str]]:
    """
    One API call. ``names`` must be non-empty deduped list.
    Returns lowercased stripped name -> https URL or None.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or not names:
        return {}
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed; skipping URL resolve")
        return {}

    client = OpenAI(api_key=key)
    model = os.getenv("COMPANY_URL_OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    payload = [
        {"name": (n or "")[:160]}
        for n in names
    ]
    user = (
        "For each company name, return the single best official corporate website "
        "homepage URL if you are highly confident it exists. Otherwise use an empty string. "
        "Only https URLs on real corporate domains (no app stores, no social profiles, "
        "no news articles). Return JSON only with this exact shape:\n"
        '{"results":[{"name":"<exact input name>","url":"https://..." or ""}, ...]}\n\n'
        f"NAMES_JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You only output valid JSON matching the requested shape.",
                },
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=1200,
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
    except Exception:
        logger.exception("OpenAI company URL batch resolve failed")
        return {}

    want = {n.strip().lower() for n in names}
    out: dict[str, Optional[str]] = {}
    for row in data.get("results") or []:
        if not isinstance(row, dict):
            continue
        nm = str(row.get("name") or "").strip().lower()
        if nm not in want:
            continue
        url = str(row.get("url") or "").strip()
        if _looks_ok_https(url):
            out[nm] = url
        else:
            out[nm] = None
    return out


def batch_resolve_company_homepage_urls(names: list[str]) -> dict[str, Optional[str]]:
    """
    Resolve a list of company names to optional https homepages.
    Keys in the returned dict are ``name.strip().lower()`` for stable joins.
    """
    if not openai_url_resolve_enabled():
        return {}

    uniq: list[str] = []
    seen: set[str] = set()
    for raw in names:
        n = (raw or "").strip()
        if not n:
            continue
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(n)

    merged: dict[str, Optional[str]] = {}
    pending: list[str] = []
    for n in uniq:
        ck = n.lower()
        hit = _cache_get_url(ck)
        if hit:
            merged[ck] = hit
        else:
            pending.append(n)

    chunk = 22
    for i in range(0, len(pending), chunk):
        part = pending[i : i + chunk]
        if not part:
            break
        got = _batch_openai_urls(part)
        for n in part:
            ck = n.lower()
            u = got.get(ck)
            if u and _looks_ok_https(u):
                u = u.strip()
                merged[ck] = u
                _cache_set_url(ck, u)
            else:
                merged[ck] = None
    return merged


def resolve_homepage_urls_for_companies(companies: list[Any]) -> dict[int, str]:
    """
    Given ORM ``Company`` rows, return ``{company.id: https_url}`` for rows that
    lack a usable ``website`` and lack signal evidence URLs (caller should mirror
    ``enrich_lead_link_fields`` gating — this helper only batches names).
    """
    from app.services.lead_primary_link import (
        _looks_like_http_url,
        first_evidence_http_url,
    )

    names: list[str] = []
    id_for_name: dict[str, int] = {}
    for c in companies:
        if c is None:
            continue
        if _looks_like_http_url(getattr(c, "website", None)):
            continue
        if first_evidence_http_url(getattr(c, "signals", None) or []):
            continue
        n = (getattr(c, "name", None) or "").strip()
        if not n:
            continue
        k = n.lower()
        if k not in id_for_name:
            id_for_name[k] = int(c.id)
            names.append(n)

    resolved = batch_resolve_company_homepage_urls(names)
    out: dict[int, str] = {}
    for n in names:
        k = n.lower()
        url = resolved.get(k)
        if url and _looks_ok_https(url):
            cid = id_for_name.get(k)
            if cid is not None:
                out[cid] = url
    return out

"""Hunter.io email discovery client for SCOUT contact enrichment."""
from __future__ import annotations

import os
from typing import Any

import requests

from app.services.apollo_client import recommended_prospect_titles

HUNTER_BASE_URL = "https://api.hunter.io/v2"
HUNTER_DOMAIN_SEARCH_PATH = "/domain-search"
HUNTER_EMAIL_FINDER_PATH = "/email-finder"

# Confidence bars for accepting a Hunter address as a *primary* outreach recipient.
# These were 50/60, which let low-confidence pattern guesses through — a big share of
# the ~50% hard-bounce rate. Raised and made env-tunable; Hunter's own verification
# status (below) is also enforced so addresses it flags "invalid" are rejected.
MIN_FINDER_SCORE = int(os.getenv("HUNTER_MIN_FINDER_SCORE", "85") or "85")
MIN_DOMAIN_CONFIDENCE = int(os.getenv("HUNTER_MIN_DOMAIN_CONFIDENCE", "80") or "80")


class HunterConfigError(Exception):
    """Raised when Hunter.io is not configured."""


class HunterAPIError(Exception):
    """Raised when Hunter rejects or fails a request."""


def hunter_contact_enabled() -> bool:
    """Hunter is on when HUNTER_API_KEY is set unless CONTACT_USE_HUNTER=false."""
    key = (os.getenv("HUNTER_API_KEY") or "").strip()
    if not key:
        return False
    flag = (os.getenv("CONTACT_USE_HUNTER") or "true").strip().lower()
    return flag not in ("0", "false", "no", "off")


class HunterClient:
    def __init__(self, api_key: str | None = None, base_url: str = HUNTER_BASE_URL):
        self.api_key = (api_key or os.getenv("HUNTER_API_KEY") or "").strip()
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise HunterConfigError("Missing HUNTER_API_KEY")

    def find_email(
        self,
        *,
        domain: str | None = None,
        company: str | None = None,
        first_name: str,
        last_name: str,
        max_duration: int = 10,
    ) -> dict[str, Any] | None:
        clean_domain = _clean_domain(domain)
        params: dict[str, Any] = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "max_duration": max(3, min(int(max_duration or 10), 20)),
        }
        if clean_domain:
            params["domain"] = clean_domain
        elif company:
            params["company"] = company.strip()
        else:
            raise HunterConfigError("domain or company is required for email finder")

        data = self._get(HUNTER_EMAIL_FINDER_PATH, params)
        payload = data.get("data") if isinstance(data, dict) else None
        if not isinstance(payload, dict):
            return None
        email = (payload.get("email") or "").strip()
        score = int(payload.get("score") or 0)
        if not email or score < MIN_FINDER_SCORE:
            return None
        verification = payload.get("verification") if isinstance(payload.get("verification"), dict) else {}
        if (verification.get("status") or "").lower() == "invalid":
            return None
        return _normalize_prospect(payload, source="hunter_finder")

    def domain_search(
        self,
        *,
        domain: str | None = None,
        company: str | None = None,
        department: str | None = "operations,management,executive",
        limit: int = 10,
    ) -> dict[str, Any]:
        clean_domain = _clean_domain(domain)
        params: dict[str, Any] = {"limit": max(1, min(int(limit or 10), 10))}
        if clean_domain:
            params["domain"] = clean_domain
        elif company:
            params["company"] = company.strip()
        else:
            raise HunterConfigError("domain or company is required for domain search")
        if department:
            params["department"] = department

        data = self._get(HUNTER_DOMAIN_SEARCH_PATH, params)
        emails = []
        if isinstance(data, dict):
            block = data.get("data")
            if isinstance(block, dict):
                emails = block.get("emails") or []
        return {
            "emails": [_normalize_domain_email(row) for row in emails if isinstance(row, dict)],
            "meta": data.get("meta") if isinstance(data, dict) else {},
        }

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query = {k: v for k, v in params.items() if v is not None and v != ""}
        query["api_key"] = self.api_key
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=query,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise HunterAPIError(f"Hunter request failed: {exc}") from exc

        if response.status_code >= 400:
            raise HunterAPIError(
                f"Hunter rejected request ({response.status_code}): {response.text[:500]}"
            )
        return response.json() if response.content else {}


def pick_best_domain_email(
    emails: list[dict[str, Any]],
    *,
    industry: str | None = None,
    min_confidence: int = MIN_DOMAIN_CONFIDENCE,
) -> dict[str, Any] | None:
    """Choose the best operational buyer email from a domain-search result."""
    preferred = [t.lower() for t in recommended_prospect_titles(industry)]
    best: dict[str, Any] | None = None
    best_score = -1

    for row in emails:
        email = (row.get("email") or "").strip()
        confidence = int(row.get("confidence") or 0)
        if not email or confidence < min_confidence:
            continue
        # Skip anything Hunter itself flags undeliverable, regardless of confidence.
        if (row.get("verification_status") or "").lower() == "invalid":
            continue
        position = (row.get("position") or row.get("title") or "").lower()
        rank = confidence
        if any(token in position for token in ("operation", "automation", "robot", "warehouse", "plant", "facilit")):
            rank += 25
        if any(pref.split()[-1] in position for pref in preferred if pref):
            rank += 15
        dept = (row.get("department") or "").lower()
        if dept in ("operations", "management", "executive"):
            rank += 10
        if rank > best_score:
            best_score = rank
            best = row
    return best


def _normalize_prospect(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    first = payload.get("first_name") or ""
    last = payload.get("last_name") or ""
    return {
        "first_name": first,
        "last_name": last,
        "name": " ".join(x for x in [first, last] if x),
        "title": payload.get("position") or payload.get("title"),
        "email": payload.get("email") or payload.get("value"),
        "confidence": payload.get("score") or payload.get("confidence"),
        "linkedin_url": payload.get("linkedin_url") or payload.get("linkedin"),
        "organization_name": payload.get("company"),
        "organization_domain": payload.get("domain"),
        "source": source,
    }


def _normalize_domain_email(row: dict[str, Any]) -> dict[str, Any]:
    first = row.get("first_name") or ""
    last = row.get("last_name") or ""
    verification = row.get("verification") if isinstance(row.get("verification"), dict) else {}
    return {
        "first_name": first,
        "last_name": last,
        "name": " ".join(x for x in [first, last] if x),
        "title": row.get("position") or row.get("position_raw"),
        "email": row.get("value") or row.get("email"),
        "confidence": row.get("confidence"),
        "department": row.get("department"),
        "verification_status": verification.get("status"),
        "linkedin_url": row.get("linkedin"),
        "source": "hunter_domain",
    }


def _clean_domain(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower()
    raw = raw.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    return raw.split("/", 1)[0] or None

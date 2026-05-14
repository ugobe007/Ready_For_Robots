"""Apollo.io prospect search client for SCOUT sales workflows."""
from __future__ import annotations

import os
from typing import Any

import requests


APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
APOLLO_PEOPLE_SEARCH_PATH = "/mixed_people/api_search"


class ApolloConfigError(Exception):
    """Raised when Apollo is not configured."""


class ApolloAPIError(Exception):
    """Raised when Apollo rejects or fails a request."""


DEFAULT_DECISION_MAKER_TITLES = [
    "VP Operations",
    "Director of Operations",
    "Chief Operating Officer",
    "Head of Automation",
    "Director of Automation",
]

INDUSTRY_DECISION_MAKER_TITLES: dict[str, list[str]] = {
    "logistics": ["VP Supply Chain", "Director of Warehouse Operations", "VP Operations", "Head of Automation"],
    "warehouse": ["Director of Warehouse Operations", "VP Fulfillment", "VP Supply Chain", "Head of Robotics"],
    "manufacturing": ["Plant Manager", "VP Manufacturing", "Director of Automation", "VP Operations"],
    "hospitality": ["General Manager", "VP Operations", "Director of Food and Beverage", "Director of Facilities"],
    "healthcare": ["Chief Operating Officer", "Director of Support Services", "VP Patient Experience", "Director of Facilities"],
    "retail": ["VP Store Operations", "Director of Store Operations", "Director of Loss Prevention", "VP Operations"],
    "food service": ["Director of Operations", "VP Operations", "VP Culinary", "Chief Operating Officer"],
}


def recommended_prospect_titles(industry: str | None = None, stage: str | None = None) -> list[str]:
    key = (industry or "").strip().lower()
    titles = INDUSTRY_DECISION_MAKER_TITLES.get(key, DEFAULT_DECISION_MAKER_TITLES)
    stage_key = (stage or "").strip().lower()
    if stage_key in {"proposal_requested", "quote_requested", "procurement_review"}:
        return list(dict.fromkeys(["Procurement Director", "VP Operations", *titles]))[:6]
    if stage_key in {"technical_specs_request", "needs_info"}:
        return list(dict.fromkeys(["Director of Engineering", "Director of Automation", *titles]))[:6]
    return titles[:6]


class ApolloProspectClient:
    def __init__(self, api_key: str | None = None, base_url: str = APOLLO_BASE_URL):
        self.api_key = (api_key or os.getenv("APOLLO_API_KEY") or "").strip()
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise ApolloConfigError("Missing APOLLO_API_KEY")

    def search_people(
        self,
        *,
        organization_name: str | None = None,
        organization_domain: str | None = None,
        titles: list[str] | None = None,
        locations: list[str] | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> dict[str, Any]:
        clean_titles = [x.strip() for x in (titles or []) if x and x.strip()]
        clean_locations = [x.strip() for x in (locations or []) if x and x.strip()]
        domain = _clean_domain(organization_domain)
        body: dict[str, Any] = {
            "page": max(1, int(page or 1)),
            "per_page": max(1, min(int(per_page or 10), 25)),
        }
        if clean_titles:
            body["person_titles"] = clean_titles
        if clean_locations:
            body["person_locations"] = clean_locations
        if organization_name:
            body["organization_names"] = [organization_name.strip()]
        if domain:
            # Apollo accepts organization-domain filters for people search; keep
            # organization_names as a fallback when both are available.
            body["q_organization_domains"] = domain

        if not (organization_name or domain):
            raise ApolloConfigError("organization_name or organization_domain is required")

        try:
            response = requests.post(
                f"{self.base_url}{APOLLO_PEOPLE_SEARCH_PATH}",
                headers={
                    "X-Api-Key": self.api_key,
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                json=body,
                timeout=20,
            )
        except requests.RequestException as exc:
            raise ApolloAPIError(f"Apollo request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ApolloAPIError(f"Apollo rejected prospect search ({response.status_code}): {response.text[:500]}")

        data = response.json() if response.content else {}
        people = data.get("people") or data.get("contacts") or data.get("prospects") or []
        return {
            "prospects": [_normalize_person(person) for person in people if isinstance(person, dict)],
            "pagination": data.get("pagination") or {},
            "request": {
                "organization_name": organization_name,
                "organization_domain": domain,
                "titles": clean_titles,
                "locations": clean_locations,
                "page": body["page"],
                "per_page": body["per_page"],
            },
        }


def _normalize_person(person: dict[str, Any]) -> dict[str, Any]:
    org = person.get("organization") if isinstance(person.get("organization"), dict) else {}
    first = person.get("first_name") or ""
    last = person.get("last_name") or ""
    return {
        "id": person.get("id"),
        "first_name": first,
        "last_name": last,
        "name": person.get("name") or " ".join(x for x in [first, last] if x),
        "title": person.get("title"),
        "email": person.get("email"),
        "email_status": person.get("email_status"),
        "linkedin_url": person.get("linkedin_url"),
        "city": person.get("city"),
        "state": person.get("state"),
        "country": person.get("country"),
        "organization_name": org.get("name") or person.get("organization_name"),
        "organization_domain": org.get("primary_domain") or org.get("website_url") or person.get("organization_domain"),
        "source": "apollo",
    }


def _clean_domain(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower()
    raw = raw.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    return raw.split("/", 1)[0] or None

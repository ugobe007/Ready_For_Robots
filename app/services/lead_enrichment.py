"""
Lead enrichment — website lookup, Apollo contact fill, email verification.

Used by intelligence scraper (auto on ingest), admin enrich endpoint, and Cal bulk send.
"""
from __future__ import annotations

import logging
import os
import re
import socket
from typing import Any, Optional

from app.models.company import Company
from app.models.crm import CrmAccount
from app.services.apollo_client import (
    ApolloAPIError,
    ApolloConfigError,
    ApolloProspectClient,
    recommended_prospect_titles,
)
from app.services.company_domain import normalize_website_domain, persist_company_domain, resolve_outreach_domain
from app.services.outreach_email_inference import (
    infer_cc_outreach_emails,
    infer_primary_outreach_email,
)
from app.services.website_inference import sleep_between_lookups, try_duckduckgo_company_website

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def infer_sales_email(domain: str | None, industry: str | None = None) -> str | None:
    """Industry-aware default TO address when no verified contact exists."""
    return infer_primary_outreach_email(domain, industry)


def enrich_company_website(company: Company, *, sleep_s: float = 0.75) -> str | None:
    """
    Resolve and persist official website when missing.

    Waterfall (pythh-style): OpenAI homepage batch → DuckDuckGo → brand slug domain.
    """
    if company.website and str(company.website).strip():
        return company.website

    name = (company.name or "").strip()
    if not name:
        return None

    found: str | None = None
    source = "unknown"

    try:
        from app.services.company_url_openai import (
            batch_resolve_company_homepage_urls,
            openai_url_resolve_enabled,
        )

        if openai_url_resolve_enabled():
            hit = batch_resolve_company_homepage_urls([name]).get(name.lower())
            if hit:
                found = hit
                source = "openai"
    except Exception as exc:
        logger.debug("OpenAI website resolve skipped for %r: %s", name, exc)

    if not found:
        found = try_duckduckgo_company_website(name)
        if found:
            source = "duckduckgo"
        if sleep_s:
            sleep_between_lookups(sleep_s)

    if not found:
        domain = resolve_outreach_domain(company)
        if domain:
            persist_company_domain(company, domain)
            found = company.website
            source = "brand_slug"

    if found and source != "brand_slug":
        company.website = found

    if found:
        logger.info("Website enriched (%s): %s → %s", source, name, found)
    return found


def apollo_contact_email(
    company_name: str,
    *,
    domain: str | None = None,
    industry: str | None = None,
) -> dict[str, Any] | None:
    """
    Find a verified decision-maker email via Apollo People Search.
    Returns normalized prospect dict or None if Apollo unavailable / no match.
    """
    try:
        client = ApolloProspectClient()
    except ApolloConfigError:
        return None

    titles = recommended_prospect_titles(industry)
    try:
        result = client.search_people(
            organization_name=company_name,
            organization_domain=domain,
            titles=titles,
            per_page=5,
        )
    except ApolloAPIError as exc:
        logger.warning("Apollo search failed for %r: %s", company_name, exc)
        return None

    for prospect in result.get("prospects") or []:
        email = (prospect.get("email") or "").strip()
        if not email or "email_not_unlocked" in email:
            continue
        status = (prospect.get("email_status") or "").lower()
        if status and status not in ("verified", "guessed", "unverified", "extrapolated"):
            continue
        if not _EMAIL_RE.match(email):
            continue
        return prospect
    return None


def resolve_outreach_email(
    company: Company,
    acct: CrmAccount | None = None,
    *,
    use_apollo: bool = True,
) -> tuple[str | None, str]:
    """
    Waterfall: CRM contact_email → Apollo → sales@domain.
    Returns (email, source_label).
    """
    if acct and (acct.contact_email or "").strip():
        return acct.contact_email.strip(), "crm_contact"

    domain = outreach_domain(company, acct)

    if use_apollo and os.getenv("APOLLO_API_KEY"):
        prospect = apollo_contact_email(
            company.name,
            domain=domain,
            industry=company.industry or (acct.industry if acct else None),
        )
        if prospect and prospect.get("email"):
            email = prospect["email"].strip()
            if acct:
                acct.contact_email = email
            return email, "apollo"

    inferred = infer_primary_outreach_email(
        domain,
        company.industry or (acct.industry if acct else None),
    )
    if inferred:
        if acct:
            acct.contact_email = inferred
        return inferred, "domain_inferred"

    return None, "missing"


def outreach_domain(company: Company, acct: CrmAccount | None = None) -> str | None:
    """Best domain for role-inbox inference — company website, then CRM account website."""
    return resolve_outreach_domain(company, acct)


def verify_email_deliverable(email: str) -> tuple[bool, str]:
    """
    Pre-send deliverability check.
    - ZERO_BOUNCE_API_KEY set → API verify (accurate)
    - Otherwise → syntax + domain resolves (free baseline)
    """
    email = (email or "").strip().lower()
    if not email or not _EMAIL_RE.match(email):
        return False, "invalid_format"

    local, _, domain = email.partition("@")
    if local in ("noreply", "no-reply", "donotreply", "postmaster", "abuse"):
        return False, "role_blocked"

    zb_key = (os.getenv("ZERO_BOUNCE_API_KEY") or os.getenv("ZEROBOUNCE_API_KEY") or "").strip()
    if zb_key:
        return _verify_zerobounce(email, zb_key)

    if not _domain_resolves(domain):
        return False, "domain_no_dns"
    return True, "syntax_dns_ok"


def _domain_resolves(domain: str) -> bool:
    try:
        socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        return False


def _verify_zerobounce(email: str, api_key: str) -> tuple[bool, str]:
    import urllib.parse
    import urllib.request
    import json

    url = (
        "https://api.zerobounce.net/v2/validate?"
        + urllib.parse.urlencode({"email": email, "api_key": api_key})
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ReadyForRobots/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning("ZeroBounce check failed for %s: %s", email, exc)
        return _domain_resolves(email.split("@", 1)[1]), "zerobounce_error_fallback"

    status = (data.get("status") or "").lower()
    if status in ("valid", "catch-all"):
        return True, f"zerobounce_{status}"
    return False, f"zerobounce_{status or 'invalid'}"


def enrich_company_and_contact(
    company: Company,
    acct: CrmAccount | None = None,
    *,
    sleep_s: float = 0.75,
    use_apollo: bool = True,
) -> dict[str, Any]:
    """
    Full enrichment pass: website → contact email waterfall.
    Mutates company/acct in place; caller commits.
    """
    out: dict[str, Any] = {
        "company_id": company.id,
        "name": company.name,
        "website_before": company.website,
        "website_after": company.website,
        "email": None,
        "email_source": None,
    }

    if not company.website:
        found = enrich_company_website(company, sleep_s=sleep_s)
        out["website_after"] = found or company.website
    if company.website and acct and not acct.website:
        acct.website = company.website

    email, source = resolve_outreach_email(company, acct, use_apollo=use_apollo)
    out["email"] = email
    out["email_source"] = source
    return out

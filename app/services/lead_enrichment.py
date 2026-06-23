"""
Lead enrichment — website lookup, Apollo contact fill, email verification.

Used by intelligence scraper (auto on ingest), admin enrich endpoint, and Cal bulk send.
"""
from __future__ import annotations

import logging
import os
import re
import socket
from typing import Any, Optional, TYPE_CHECKING

from app.models.company import Company

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
from app.models.crm import CrmAccount
from app.services.apollo_client import (
    ApolloAPIError,
    ApolloConfigError,
    ApolloProspectClient,
    recommended_prospect_titles,
)
from app.services.contact_free_sources import (
    apollo_contact_enabled,
    decision_maker_records,
    fetch_website_mailto_email,
    infer_person_email_from_decision_makers,
    pick_signal_outreach_email,
)
from app.services.hunter_client import (
    HunterAPIError,
    HunterClient,
    HunterConfigError,
    hunter_contact_enabled,
    pick_best_domain_email,
)
from app.services.company_domain import normalize_website_domain, persist_company_domain, resolve_outreach_domain, is_trusted_outreach_domain
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
    existing = normalize_website_domain(company.website)
    if existing and is_trusted_outreach_domain(existing):
        return company.website
    if existing and not is_trusted_outreach_domain(existing):
        logger.info("Clearing untrusted website for %r: %s", company.name, company.website)
        company.website = None
        if hasattr(company, "website_domain"):
            company.website_domain = None

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
        if is_trusted_outreach_domain(normalize_website_domain(found)):
            company.website = found
        else:
            found = None

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


def hunter_contact_email(
    company_name: str,
    *,
    domain: str | None = None,
    industry: str | None = None,
    company: Company | None = None,
    contacts: list | None = None,
) -> dict[str, Any] | None:
    """
    Find a decision-maker email via Hunter.io Email Finder or Domain Search.
    Uses named decision makers when available; otherwise ranks domain emails by title.
    """
    if not hunter_contact_enabled():
        return None
    try:
        client = HunterClient()
    except HunterConfigError:
        return None

    source_company = company
    dm_records = decision_maker_records(source_company, contacts) if source_company else []

    for dm in dm_records[:2]:
        first = (dm.get("first_name") or dm.get("first") or "").strip()
        last = (dm.get("last_name") or dm.get("last") or "").strip()
        if not first or not last:
            continue
        try:
            prospect = client.find_email(
                domain=domain,
                company=company_name,
                first_name=first,
                last_name=last,
            )
        except HunterAPIError as exc:
            logger.warning("Hunter finder failed for %r: %s", company_name, exc)
            break
        if prospect and prospect.get("email"):
            if not prospect.get("title"):
                prospect["title"] = dm.get("title")
            return prospect

    if not domain and not company_name:
        return None

    try:
        search = client.domain_search(domain=domain, company=company_name)
    except HunterAPIError as exc:
        logger.warning("Hunter domain search failed for %r: %s", company_name, exc)
        return None

    best = pick_best_domain_email(search.get("emails") or [], industry=industry)
    if best and best.get("email"):
        return best
    return None


def resolve_outreach_email(
    company: Company,
    acct: CrmAccount | None = None,
    *,
    use_apollo: bool | None = None,
    signal_texts: list[str] | None = None,
    contacts: list | None = None,
) -> tuple[str | None, str, str | None]:
    """
    Waterfall: CRM → Apollo (opt-in) → Hunter → signal → person guess → mailto → role inbox.
    Returns (email, source_label, contact_title).
    """
    if acct and (acct.contact_email or "").strip():
        return acct.contact_email.strip(), "crm_contact", None

    domain = outreach_domain(company, acct)
    industry = company.industry or (acct.industry if acct else None)

    if use_apollo is None:
        use_apollo = apollo_contact_enabled()

    if use_apollo:
        prospect = apollo_contact_email(
            company.name,
            domain=domain,
            industry=industry,
        )
        if prospect and prospect.get("email"):
            email = prospect["email"].strip()
            if acct:
                acct.contact_email = email
            return email, "apollo", prospect.get("title")

    prospect = hunter_contact_email(
        company.name,
        domain=domain,
        industry=industry,
        company=company,
        contacts=contacts,
    )
    if prospect and prospect.get("email"):
        email = prospect["email"].strip()
        if _EMAIL_RE.match(email):
            if acct:
                acct.contact_email = email
            source = prospect.get("source") or "hunter"
            label = "hunter_domain" if source == "hunter_domain" else "hunter"
            return email, label, prospect.get("title")

    texts = signal_texts or []
    if not texts:
        meta = company.crm_metadata or {}
        for key in ("signal_snippets", "recent_signals"):
            for item in meta.get(key) or []:
                if isinstance(item, str) and item.strip():
                    texts.append(item.strip())

    signal_email = pick_signal_outreach_email(texts, domain)
    if signal_email:
        if acct:
            acct.contact_email = signal_email
        return signal_email, "signal_email", None

    person_email, _pattern, dm_title = infer_person_email_from_decision_makers(
        company, contacts, domain
    )
    if person_email:
        if acct:
            acct.contact_email = person_email
        return person_email, "person_inferred", dm_title

    if domain:
        mailto_email = fetch_website_mailto_email(domain)
        if mailto_email:
            if acct:
                acct.contact_email = mailto_email
            return mailto_email, "website_mailto", None

    inferred = infer_primary_outreach_email(domain, industry)
    if inferred:
        if acct:
            acct.contact_email = inferred
        return inferred, "domain_inferred", None

    return None, "missing", None


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


def persist_outreach_contact(
    company: Company,
    db: "Session",
    *,
    email: str,
    source: str,
    title: str | None = None,
) -> bool:
    """
    Write a Contact row + crm_metadata.outreach_email when waterfall finds an address.
    Returns True if a new contact row was created.
    """
    from app.models.contact import Contact

    email = (email or "").strip().lower()
    if not email or not _EMAIL_RE.match(email):
        return False

    existing = (
        db.query(Contact.id)
        .filter(Contact.company_id == company.id, Contact.email == email)
        .first()
    )
    created = False
    if not existing:
        source_titles = {
            "apollo": "Apollo prospect",
            "hunter": "Hunter prospect",
            "hunter_domain": "Hunter domain match",
            "signal_email": "Signal contact",
            "person_inferred": "Inferred person email",
            "website_mailto": "Website contact",
            "domain_inferred": "Role inbox",
        }
        source_scores = {
            "apollo": 70,
            "hunter": 78,
            "hunter_domain": 72,
            "website_mailto": 62,
            "signal_email": 58,
            "person_inferred": 50,
            "domain_inferred": 45,
        }
        role_title = title or source_titles.get(source, "Outreach contact")
        db.add(
            Contact(
                company_id=company.id,
                first_name="Outreach",
                last_name="",
                title=role_title,
                email=email,
                confidence_score=source_scores.get(source, 45),
            )
        )
        created = True

    meta = dict(company.crm_metadata or {})
    meta["outreach_email"] = email
    meta["outreach_email_source"] = source
    company.crm_metadata = meta
    db.add(company)
    return created


def enrich_company_and_contact(
    company: Company,
    acct: CrmAccount | None = None,
    *,
    sleep_s: float = 0.75,
    use_apollo: bool | None = None,
    db: "Session | None" = None,
    persist_contact: bool = False,
) -> dict[str, Any]:
    """
    Full enrichment pass: website → contact email waterfall.
    Mutates company/acct in place; caller commits when persist_contact is False.
    """
    out: dict[str, Any] = {
        "company_id": company.id,
        "name": company.name,
        "website_before": company.website,
        "website_after": company.website,
        "email": None,
        "email_source": None,
        "contact_persisted": False,
    }

    if not company.website:
        found = enrich_company_website(company, sleep_s=sleep_s)
        out["website_after"] = found or company.website
    if company.website and acct and not acct.website:
        acct.website = company.website

    signal_texts: list[str] = []
    contacts: list = []
    if db is not None:
        from app.models.contact import Contact
        from app.models.signal import Signal
        from app.services.signal_text_normalize import strip_signal_html

        signals = (
            db.query(Signal)
            .filter(Signal.company_id == company.id)
            .order_by(Signal.created_at.desc())
            .limit(12)
            .all()
        )
        signal_texts = [
            strip_signal_html(getattr(s, "signal_text", "") or "")
            for s in signals
            if getattr(s, "signal_text", None)
        ]
        contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()

    email, source, contact_title = resolve_outreach_email(
        company,
        acct,
        use_apollo=use_apollo,
        signal_texts=signal_texts,
        contacts=contacts,
    )
    out["email"] = email
    out["email_source"] = source

    if email and persist_contact and db is not None:
        out["contact_persisted"] = persist_outreach_contact(
            company, db, email=email, source=source, title=contact_title
        )

    return out


def enrich_company_contact_with_fallback(
    company: Company,
    db: "Session",
    *,
    sleep_s: float = 0.5,
    use_apollo: bool | None = None,
) -> dict[str, Any]:
    """Website lookup + free contact stack + optional Apollo; persists when email found."""
    out = enrich_company_and_contact(
        company,
        acct=None,
        sleep_s=sleep_s,
        use_apollo=use_apollo,
        db=db,
        persist_contact=True,
    )
    db.commit()
    return out

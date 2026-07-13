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
from app.services.email_address import normalize_recipient_email
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
        # Only accept emails Apollo itself marks VERIFIED. "guessed" / "unverified" /
        # "extrapolated" are name-derived guesses — and because the Apollo source is
        # trusted by the send gate, an unverified Apollo address would bypass the guard
        # and bounce. Requiring verified keeps Apollo in the trusted set safely.
        status = (prospect.get("email_status") or "").lower()
        if status != "verified":
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
    def _remember(addr: str, src: str) -> None:
        """Durably record a verified contact + its true source on the company."""
        if company is None or not addr:
            return
        base = getattr(company, "crm_metadata", None)
        meta = dict(base) if isinstance(base, dict) else {}
        meta["outreach_email"] = addr.strip().lower()
        meta["outreach_email_source"] = src
        meta.pop("outreach_email_status", None)      # clear any prior quarantine
        meta.pop("outreach_quarantine_reason", None)
        company.crm_metadata = meta

    # URL-first policy: resolve + verify the company website BEFORE looking up any email.
    # No URL, or a dead (non-resolving) URL, means we must not guess an address — those
    # guesses at dead domains were the dominant bounce class. Quarantine the email to null.
    # A transient DNS failure is non-destructive: we skip this pass without nulling.
    require_url = (os.getenv("CAL_REQUIRE_VERIFIED_URL", "1") or "1").strip().lower() in ("1", "true", "yes")
    verified_domain, url_reason = verify_outreach_url(company, acct)
    if require_url:
        if url_reason in ("no_url", "nxdomain"):
            quarantine_outreach_email(company, acct, url_reason)
            return None, f"quarantined_url:{url_reason}", None
        if url_reason == "temporary":
            # Don't null a stored address over a momentary resolver blip — retry next cycle.
            return None, "url_unverified_temporary", None

    if acct and (acct.contact_email or "").strip():
        stored = acct.contact_email.strip()
        base = getattr(company, "crm_metadata", None)
        meta = base if isinstance(base, dict) else {}
        if (meta.get("outreach_email") or "").strip().lower() == stored.lower():
            # Return the true recorded source so verified emails stay trusted and
            # guessed emails (laundered onto contact_email) do not pass as real.
            src = (meta.get("outreach_email_source") or "").strip().lower() or "crm_contact"
            return stored, src, None
        return stored, "crm_contact", None

    # Use the URL we already verified above (falls back to best-effort when the policy
    # toggle is off). Every inferred/role/person address below is built on this domain.
    domain = verified_domain or outreach_domain(company, acct)
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
            _remember(email, "apollo")
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
            _remember(email, label)
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
        _remember(signal_email, "signal_email")
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
            _remember(mailto_email, "website_mailto")
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
    email = normalize_recipient_email(email) or ""
    if not email or not _EMAIL_RE.match(email):
        return False, "invalid_format"

    local, _, domain = email.partition("@")
    if local in ("noreply", "no-reply", "donotreply", "postmaster", "abuse"):
        return False, "role_blocked"

    zb_key = (os.getenv("ZERO_BOUNCE_API_KEY") or os.getenv("ZEROBOUNCE_API_KEY") or "").strip()
    if zb_key:
        # ZeroBounce bills per validation — cache every definitive result so we never pay
        # twice for the same address. A mailbox's deliverability is stable over weeks.
        cached = _zb_cache_get(email)
        if cached is not None:
            return cached
        result = _verify_zerobounce(email, zb_key)
        if not result[1].endswith("error_fallback"):  # don't cache transient API failures
            _zb_cache_set(email, result)
        return result

    if not _domain_resolves(domain):
        return False, "domain_no_dns"
    return True, "syntax_dns_ok"


def _zb_redis():
    url = (os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def _zb_cache_get(email: str) -> tuple[bool, str] | None:
    client = _zb_redis()
    if not client:
        return None
    try:
        raw = client.get(f"zb:verify:{email.lower()}")
    except Exception:
        return None
    if not raw:
        return None
    ok, _, reason = str(raw).partition("|")
    return (ok == "1", f"{reason or 'zerobounce'}:cached")


def _zb_cache_set(email: str, result: tuple[bool, str]) -> None:
    client = _zb_redis()
    if not client:
        return
    try:
        days = float(os.getenv("ZERO_BOUNCE_CACHE_DAYS", "30") or "30")
        client.set(
            f"zb:verify:{email.lower()}",
            f"{'1' if result[0] else '0'}|{result[1]}",
            ex=int(days * 86400),
        )
    except Exception:
        pass


def _domain_dns_status(domain: str) -> str:
    """Classify a domain's DNS resolution: 'ok' | 'nxdomain' | 'temporary'.

    We distinguish a permanently dead domain (name does not exist) from a transient
    resolver failure so the URL-quarantine policy never destructively nulls a good
    address over a momentary DNS blip.
    """
    if not domain:
        return "nxdomain"
    try:
        socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
        return "ok"
    except socket.gaierror as exc:
        permanent = {
            getattr(socket, "EAI_NONAME", object()),
            getattr(socket, "EAI_NODATA", object()),
        }
        if getattr(exc, "errno", None) in permanent:
            return "nxdomain"
        return "temporary"
    except Exception:
        return "temporary"


def _domain_resolves(domain: str) -> bool:
    return _domain_dns_status(domain) == "ok"


def verify_outreach_url(company: Company, acct: CrmAccount | None = None) -> tuple[str | None, str]:
    """Resolve + verify the company's website URL BEFORE any email lookup.

    Returns ``(verified_domain, reason)`` where reason is one of:
      - ``ok``        → domain resolves; safe to look up / infer an address on it
      - ``no_url``    → no website/domain at all
      - ``nxdomain``  → domain is registered-looking but does not resolve (dead)
      - ``temporary`` → DNS lookup failed transiently (do NOT quarantine; retry later)

    Policy: guessed addresses at dead/absent domains were the dominant bounce class, so
    a missing or unresolvable URL must block the waterfall entirely.
    """
    domain = outreach_domain(company, acct)
    if not domain:
        return None, "no_url"
    status = _domain_dns_status(domain)
    if status == "ok":
        return domain, "ok"
    if status == "nxdomain":
        return None, "nxdomain"
    return None, "temporary"


def quarantine_outreach_email(
    company: Company | None, acct: CrmAccount | None, reason: str
) -> None:
    """Null any stored/guessed address and stamp the company URL-quarantined.

    No send path will use a quarantined address; it stays null until a verified URL
    and a verified contact are found (re-enrichment clears it).
    """
    if acct is not None:
        acct.contact_email = None
    if company is not None:
        base = getattr(company, "crm_metadata", None)
        meta = dict(base) if isinstance(base, dict) else {}
        meta["outreach_email"] = None
        meta["outreach_email_source"] = None
        meta["outreach_email_status"] = "quarantined"
        meta["outreach_quarantine_reason"] = reason
        company.crm_metadata = meta


# Terminal delivery states — an address in any of these must never be emailed again.
_SUPPRESSED_STATUSES = ("bounced", "complained", "suppressed")


def address_previously_bounced(db: "Session", email: str) -> bool:
    """True if we've ever recorded a bounce/complaint/suppression to this address.

    Durable, global suppression with no extra schema: outreach_messages already
    records terminal delivery problems, so a prior bounce is a hard signal never to
    send there again. Global (not per-company) on purpose — guessed role inboxes like
    info@domain recur across companies, and a dead mailbox stays dead.
    """
    normalized = (normalize_recipient_email(email) or "").lower()
    if not normalized:
        return False
    from sqlalchemy import func
    from app.models.outreach import OutreachMessage

    row = (
        db.query(OutreachMessage.id)
        .filter(
            func.lower(OutreachMessage.to_email) == normalized,
            OutreachMessage.status.in_(_SUPPRESSED_STATUSES),
        )
        .first()
    )
    return row is not None


def recent_bounce_rate(db: "Session", hours: int = 168) -> dict:
    """Trailing-window deliverability snapshot from outreach_messages.

    Returns counts + the bounce rate (bounced / total sent in the window). Powers the
    deliverability circuit breaker and the daily digest. ``bounced`` folds in complaints
    and suppressions since all three are reputation-damaging non-deliveries.
    """
    import time as _time
    from datetime import datetime, timezone
    from sqlalchemy import func
    from app.models.outreach import OutreachMessage

    since = datetime.fromtimestamp(_time.time() - hours * 3600, tz=timezone.utc)
    rows = (
        db.query(OutreachMessage.status, func.count(OutreachMessage.id))
        .filter(OutreachMessage.sent_at.isnot(None), OutreachMessage.sent_at >= since)
        .group_by(OutreachMessage.status)
        .all()
    )
    counts = {str(status or "unknown"): int(n) for status, n in rows}
    sent = sum(counts.values())
    bounced = counts.get("bounced", 0) + counts.get("complained", 0) + counts.get("suppressed", 0)
    delivered = counts.get("delivered", 0)
    return {
        "hours": hours,
        "sent": sent,
        "bounced": bounced,
        "delivered": delivered,
        "rate": round(bounced / sent, 4) if sent else 0.0,
        "by_status": counts,
    }


# Email sources that came from a real observation/verification, not a name-derived guess.
# hunter_domain = Hunter domain-search hit (a real person at the company), verified by
# Hunter — as trustworthy as a Hunter finder result. person_inferred / domain_inferred
# are name-derived GUESSES and are intentionally excluded.
_VERIFIED_EMAIL_SOURCES = frozenset(
    {"apollo", "hunter", "hunter_domain", "website_mailto", "signal_email"}
)


def company_website_domain(company: Company, acct: CrmAccount | None = None) -> str | None:
    """
    The company's REAL website domain (from the website field only) — never a
    name-derived brand-slug guess. Used to gate outreach so we don't email
    fabricated domains like hawaiian.com for "Hawaiian Airlines".
    """
    from app.services.company_domain import normalize_website_domain

    dom = normalize_website_domain(
        getattr(company, "website", None) or (getattr(acct, "website", None) if acct else None)
    )
    if dom:
        return dom
    wd = getattr(company, "website_domain", None)
    if wd and str(wd).strip():
        return normalize_website_domain(str(wd))
    return None


def outreach_recipient_trusted(
    company: Company,
    acct: CrmAccount | None,
    email: str,
    source: str,
) -> tuple[bool, str]:
    """
    Guard against bounces: trust the recipient ONLY when the address came from a
    verified provider/observation (Apollo / Hunter / Hunter domain search / website
    mailto / signal). A domain-matched *guess* (role/person inbox on the real domain)
    is NOT trusted — those mailboxes frequently do not exist and were the dominant
    bounce class (info@/name@ at valid domains).

    Rejects laundered guesses: resolve_outreach_email stores name-derived guesses
    back onto acct.contact_email, so a "crm_contact" source is NOT inherently real.
    """
    normalized = normalize_recipient_email(email) or ""
    if not normalized or "@" not in normalized:
        return False, "invalid_format"
    edom = normalized.rsplit("@", 1)[-1].strip().lower()
    if edom.startswith("www."):
        edom = edom[4:]

    if (source or "") in _VERIFIED_EMAIL_SOURCES:
        return True, source

    web = company_website_domain(company, acct)
    return False, f"unverified:{source or 'unknown'}:{edom or 'none'}~{web or 'no-website'}"


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
    if status == "valid":
        return True, "zerobounce_valid"
    # catch-all domains accept mail at SMTP time but can still silently drop it — a real
    # bounce source. During deliverability recovery reject them by default; an operator can
    # opt back in with ZERO_BOUNCE_ACCEPT_CATCH_ALL=1 once reputation is healthy.
    if status == "catch-all":
        accept = (os.getenv("ZERO_BOUNCE_ACCEPT_CATCH_ALL") or "0").strip().lower() in ("1", "true", "yes")
        return (accept, "zerobounce_catch_all" + ("" if accept else "_rejected"))
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

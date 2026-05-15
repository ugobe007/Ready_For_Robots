"""
Robot Companies API
Lead generation system for robotics vendors
Focus: Chinese companies entering U.S. market
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import os
import re
import secrets
import uuid
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.database import get_db
from app.api.auth_deps import _require_user
from app.api.crm import _ensure_default_team, _uid_uuid
from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.outreach import OutreachMessage
from app.models.robot_company import RobotCompany
from app.models.supply_outreach import SupplyOutreachMessage
from app.services.company_domain import normalize_website_domain
from app.services.email_templates import get_email_template
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.sales_learning_agent import record_sales_experience
from app.services.shared_api_cache import shared_cache_get, shared_cache_set
from app.services.vendor_scoring import compute_vendor_list_score

router = APIRouter(prefix="/api/robot-companies", tags=["robot-companies"])


class SendRobotCompanyEmailRequest(BaseModel):
    to_email: str | list[str]
    template_type: str = "intro"
    subject: Optional[str] = None
    body: Optional[str] = None


class ApproveSupplyOutreachRequest(BaseModel):
    to_email: str | list[str]
    template_type: str = "supply_pipeline"
    subject: str
    body: str
    payload: Optional[dict[str, Any]] = None


def _split_terms(*values: Any) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        raw = str(value).lower().replace("/", " ").replace("-", " ")
        for part in raw.replace("&", " ").replace(",", " ").split():
            if len(part) >= 3:
                terms.add(part.strip())
    return terms


def _robot_market_terms(rc: RobotCompany) -> set[str]:
    terms = _split_terms(rc.robot_type, rc.target_market, rc.product_category)
    aliases = {
        "amr": {"warehouse", "logistics", "fulfillment", "distribution", "material", "handling"},
        "cobot": {"manufacturing", "assembly", "industrial", "production"},
        "industrial": {"manufacturing", "assembly", "production", "factory"},
        "service": {"hospitality", "healthcare", "retail", "cleaning"},
        "vision": {"inspection", "quality", "manufacturing", "safety"},
        "humanoid": {"warehouse", "manufacturing", "service", "hospitality"},
    }
    for term in list(terms):
        terms.update(aliases.get(term, set()))
    return terms


def _lead_terms(company: Company) -> set[str]:
    profile = company.automation_profile or {}
    requirements = []
    if isinstance(profile, dict):
        requirements = profile.get("requirements") or profile.get("automation_requirements") or []
    signal_terms = [s.signal_type for s in (company.signals or [])[:5]]
    return _split_terms(company.industry, company.sub_industry, company.crm_metadata, requirements, signal_terms)


def _lead_score(company: Company, vendor_terms: set[str]) -> float:
    score = 0.0
    if company.scores:
        score += max(float(s.overall_intent_score or 0) for s in company.scores)
    lead_terms = _lead_terms(company)
    overlap = vendor_terms.intersection(lead_terms)
    score += min(25.0, len(overlap) * 6.0)
    score += min(15.0, len(company.signals or []) * 2.5)
    return round(score, 1)


def _match_buyer_leads(db: Session, rc: RobotCompany, limit: int = 3) -> list[dict[str, Any]]:
    vendor_terms = _robot_market_terms(rc)
    candidates = (
        db.query(Company)
        .options(joinedload(Company.signals), joinedload(Company.scores))
        .filter(Company.is_internal.is_(True))
        .order_by(Company.updated_at.desc().nullslast(), Company.created_at.desc().nullslast())
        .limit(300)
        .all()
    )
    ranked = sorted(
        (
            {
                "id": c.id,
                "company_name": c.name,
                "industry": c.industry,
                "location": ", ".join(x for x in [c.location_city, c.location_state] if x) or None,
                "score": _lead_score(c, vendor_terms),
                "signal": (c.signals[0].signal_text if c.signals else None),
                "signal_type": (c.signals[0].signal_type if c.signals else None),
                "why_match": _why_match(rc, c, vendor_terms),
            }
            for c in candidates
        ),
        key=lambda row: row["score"],
        reverse=True,
    )
    return [row for row in ranked if row["score"] > 0][:limit]


def _why_match(rc: RobotCompany, company: Company, vendor_terms: set[str]) -> str:
    overlap = sorted(vendor_terms.intersection(_lead_terms(company)))
    if overlap:
        return f"Matches {rc.company_name}'s market around {', '.join(overlap[:4])}."
    if company.industry and rc.target_market:
        return f"{company.industry} lead aligns with target market: {rc.target_market}."
    return "Buyer has active automation signals that may fit this robot category."


ROLE_INBOXES = ("partnerships", "events", "marketing", "sales")
CONTACT_RESEARCH_PATHS = (
    "",
    "/about",
    "/company",
    "/leadership",
    "/team",
    "/contact",
    "/partners",
    "/partnerships",
    "/events",
)
CONTACT_RESEARCH_TITLES = (
    "chief revenue officer",
    "chief marketing officer",
    "chief commercial officer",
    "vp sales",
    "vice president sales",
    "head of sales",
    "head of partnerships",
    "partnerships",
    "business development",
    "channel",
    "marketing",
    "events",
    "sales",
    "founder",
    "ceo",
)


def _reply_domain() -> str:
    return (os.getenv("SCOUT_REPLY_DOMAIN") or "readyforrobots.com").strip()


def _supply_reply_address(reply_token: str) -> str:
    local = (os.getenv("SUPPLY_REPLY_LOCAL_PART") or "supply").strip()
    return f"{local}+{reply_token}@{_reply_domain()}"


def _contact_strategy(rc: RobotCompany, research: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    domain = normalize_website_domain(getattr(rc, "website", None))
    role_inboxes = _role_inbox_emails(domain)
    research = research or {}
    decision_maker_candidates = _decision_maker_email_candidates(rc, domain, research)
    targets = []
    partnerships_email = _clean_email(getattr(rc, "partnerships_contact", None))
    sales_email = _clean_email(getattr(rc, "sales_contact", None))
    contact_email = _clean_email(getattr(rc, "contact_email", None))
    if partnerships_email:
        targets.append({"role": "Partnerships", "contact": partnerships_email, "priority": 1, "source": "stored"})
    if sales_email:
        targets.append({"role": "Sales leadership", "contact": sales_email, "priority": 2, "source": "stored"})
    if contact_email:
        targets.append({"role": "General contact", "contact": contact_email, "priority": 3, "source": "stored"})
    targets.extend(decision_maker_candidates)
    targets.extend(role_inboxes)
    targets = _dedupe_contact_targets(targets)
    if not targets:
        targets.append({"role": "Research needed", "contact": None, "priority": 9, "source": "missing"})
    policy_recipients = _dedupe_emails(
        [target["contact"] for target in role_inboxes]
        + [target["contact"] for target in decision_maker_candidates]
    )
    return {
        "primary": targets[0],
        "targets": targets,
        "recommended_to": policy_recipients,
        "communication_policy": {
            "role_inboxes": [target["contact"] for target in role_inboxes],
            "decision_maker_patterns": [
                "first.last@domain",
                "firstinitiallast@domain",
                "last@domain",
                "first@domain",
            ],
            "research_sources": [
                source
                for source in [
                    getattr(rc, "website", None),
                    getattr(rc, "linkedin_url", None),
                    *(research.get("sources") or []),
                    *(research.get("linkedin_urls") or []),
                ]
                if source
            ],
            "researched_decision_makers": research.get("decision_makers") or [],
            "research_status": research.get("status") or "not_run",
        },
        "research_notes": [
            "Research the company URL and LinkedIn to identify current partnerships, marketing, events, sales, and business development decision makers.",
            "Look for VP Sales, Head of Partnerships, Channel, or Business Development.",
            "Send role inbox outreach to partnerships, events, marketing, and sales when direct decision-maker emails are missing.",
            "When a decision-maker name is known, verify likely email patterns before sending.",
        ],
    }


def _clean_email(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw or raw.startswith(("http://", "https://")):
        return None
    if "@" not in raw:
        return None
    return raw.strip("<> ,;")


def _role_inbox_emails(domain: Optional[str]) -> list[dict[str, Any]]:
    if not domain:
        return []
    return [
        {
            "role": f"{local.title()} inbox",
            "contact": f"{local}@{domain}",
            "priority": index + 4,
            "source": "domain_inferred",
            "needs_verification": True,
        }
        for index, local in enumerate(ROLE_INBOXES)
    ]


def _decision_maker_email_candidates(
    rc: RobotCompany,
    domain: Optional[str],
    research: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    if not domain:
        return []
    candidates = []
    for first, last, source, title in _decision_maker_names(rc, research):
        patterns = [
            (f"{first}.{last}@{domain}", "first.last"),
            (f"{first[0]}{last}@{domain}", "firstinitiallast"),
            (f"{last}@{domain}", "last"),
            (f"{first}@{domain}", "first"),
        ]
        for offset, (email, pattern) in enumerate(patterns):
            candidates.append(
                {
                    "role": f"Decision maker ({first.title()} {last.title()})",
                    "contact": email,
                    "priority": 20 + offset,
                    "source": source,
                    "title": title,
                    "pattern": pattern,
                    "needs_verification": True,
                }
            )
    return candidates


def _decision_maker_names(
    rc: RobotCompany,
    research: Optional[dict[str, Any]] = None,
) -> list[tuple[str, str, str, Optional[str]]]:
    values = [getattr(rc, "sales_contact", None), getattr(rc, "partnerships_contact", None)]
    for container in [getattr(rc, "market_intelligence", None), getattr(rc, "workflow_history", None)]:
        values.extend(_flatten_strings(container))
    names: list[tuple[str, str, str, Optional[str]]] = []
    for person in (research or {}).get("decision_makers") or []:
        first = str(person.get("first_name") or "").strip().lower()
        last = str(person.get("last_name") or "").strip().lower()
        if first and last:
            names.append((first, last, "website_research", person.get("title")))
    for value in values:
        if not value or "@" in str(value):
            continue
        for first, last in re.findall(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", str(value)):
            names.append((first.lower(), last.lower(), "decision_maker_inferred", None))
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str, str, Optional[str]]] = []
    for first, last, source, title in names:
        key = (first, last)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((first, last, source, title))
    return deduped[:3]


def _flatten_strings(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten_strings(item))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_flatten_strings(item))
        return out
    return []


def _research_robot_company_contacts(
    rc: RobotCompany,
    *,
    enabled: bool = True,
    max_pages: int = 2,
    timeout: float = 1.5,
) -> dict[str, Any]:
    if not enabled:
        return {"status": "skipped", "decision_makers": [], "sources": [], "linkedin_urls": []}
    website = getattr(rc, "website", None)
    domain = normalize_website_domain(website)
    if not website or not domain:
        return {"status": "missing_website", "decision_makers": [], "sources": [], "linkedin_urls": []}

    cache_key = f"{domain}:{getattr(rc, 'updated_at', None) or ''}"
    cached = shared_cache_get("robot_contact_research", cache_key)
    if cached:
        return cached

    decision_makers: list[dict[str, Any]] = []
    linkedin_urls: list[str] = []
    sources: list[str] = []
    for url in _contact_research_urls(website)[:max_pages]:
        html = _fetch_contact_research_page(url, timeout=timeout)
        if not html:
            continue
        sources.append(url)
        extracted = _extract_contact_research(html, url)
        decision_makers.extend(extracted["decision_makers"])
        linkedin_urls.extend(extracted["linkedin_urls"])
        if len(_dedupe_people(decision_makers)) >= 3:
            break

    decision_makers = _dedupe_people(decision_makers)[:3]
    result = {
        "status": "found" if decision_makers else ("checked" if sources else "unavailable"),
        "decision_makers": decision_makers,
        "sources": _dedupe_emails_or_urls(sources),
        "linkedin_urls": _dedupe_emails_or_urls(linkedin_urls)[:5],
    }
    shared_cache_set("robot_contact_research", cache_key, result, ttl_sec=24 * 60 * 60)
    return result


def _contact_research_urls(website: str) -> list[str]:
    base = website if "://" in str(website) else f"https://{website}"
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}"
    return [urljoin(root, path) for path in CONTACT_RESEARCH_PATHS]


def _fetch_contact_research_page(url: str, *, timeout: float) -> Optional[str]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "ReadyForRobots/1.0 (contact research)"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return None
    if response.status_code >= 400:
        return None
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type and content_type:
        return None
    return response.text[:250_000]


def _extract_contact_research(html: str, source_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    linkedin_urls = _extract_linkedin_profile_urls(soup, source_url)
    text = soup.get_text("\n", strip=True)
    candidates = _extract_people_from_text(text, source_url)
    candidates.extend(_extract_people_from_linkedin_links(soup, source_url))
    return {
        "decision_makers": _dedupe_people(candidates)[:5],
        "linkedin_urls": linkedin_urls,
    }


def _extract_linkedin_profile_urls(soup: BeautifulSoup, source_url: str) -> list[str]:
    urls = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(source_url, str(anchor.get("href") or ""))
        low = href.lower()
        if "linkedin.com/in/" in low or "linkedin.com/company/" in low:
            urls.append(href.split("?")[0].rstrip("/"))
    return _dedupe_emails_or_urls(urls)


def _extract_people_from_linkedin_links(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    people = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(source_url, str(anchor.get("href") or ""))
        if "linkedin.com/in/" not in href.lower():
            continue
        label = anchor.get_text(" ", strip=True)
        match = re.search(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", label)
        if not match:
            slug = href.rstrip("/").split("/in/", 1)[-1].split("/", 1)[0]
            match = re.match(r"([a-zA-Z]+)-([a-zA-Z]+)", slug)
        if match:
            first, last = match.group(1), match.group(2)
            people.append(
                {
                    "first_name": first.title(),
                    "last_name": last.title(),
                    "title": None,
                    "source_url": href.split("?")[0].rstrip("/"),
                    "source": "linkedin_profile_link",
                }
            )
    return people


def _extract_people_from_text(text: str, source_url: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", text or " ").strip()
    if not normalized:
        return []
    title_pattern = "|".join(re.escape(title) for title in sorted(CONTACT_RESEARCH_TITLES, key=len, reverse=True))
    patterns = [
        rf"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b[^.|\n]{{0,90}}?\b({title_pattern})\b",
        rf"\b({title_pattern})\b[^.|\n]{{0,90}}?\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b",
    ]
    people: list[dict[str, Any]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            groups = match.groups()
            if len(groups) != 3:
                continue
            if groups[0].lower() in CONTACT_RESEARCH_TITLES:
                title, first, last = groups[0], groups[1], groups[2]
            else:
                first, last, title = groups[0], groups[1], groups[2]
            if _looks_like_person_name(first, last):
                people.append(
                    {
                        "first_name": first.title(),
                        "last_name": last.title(),
                        "title": title.title(),
                        "source_url": source_url,
                        "source": "website_text",
                    }
                )
    return people


def _looks_like_person_name(first: str, last: str) -> bool:
    bad = {
        "About",
        "Contact",
        "Company",
        "Marketing",
        "Partnerships",
        "Business",
        "Development",
        "Privacy",
        "Terms",
        "Ready",
        "Robots",
    }
    if first in bad or last in bad:
        return False
    return bool(re.match(r"^[A-Z][a-z]{1,24}$", first) and re.match(r"^[A-Z][a-z]{1,24}$", last))


def _dedupe_people(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    for person in people:
        first = str(person.get("first_name") or "").strip()
        last = str(person.get("last_name") or "").strip()
        key = (first.lower(), last.lower())
        if not first or not last or key in seen:
            continue
        seen.add(key)
        deduped.append(person)
    return deduped


def _dedupe_emails_or_urls(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    deduped = []
    for value in values:
        item = str(value or "").strip()
        key = item.lower()
        if not item or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _dedupe_contact_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped = []
    for target in sorted(targets, key=lambda row: row.get("priority", 99)):
        contact = (target.get("contact") or "").strip().lower()
        if not contact or contact in seen:
            continue
        seen.add(contact)
        deduped.append(target)
    return deduped


def _dedupe_emails(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    emails = []
    for value in values:
        email = str(value or "").strip()
        if "@" not in email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)
    return emails


def _request_emails(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw_values = value
    else:
        raw_values = str(value or "").replace(";", ",").split(",")
    return _dedupe_emails(raw_values)


def _require_supply_outreach_payload(payload: ApproveSupplyOutreachRequest) -> tuple[list[str], str, str]:
    to_emails = _request_emails(payload.to_email)
    subject = (payload.subject or "").strip()
    body = (payload.body or "").strip()
    if not to_emails:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")
    if not subject:
        raise HTTPException(status_code=400, detail="Subject is required")
    if not body:
        raise HTTPException(status_code=400, detail="Body is required")
    return to_emails, subject, body


def _create_supply_outreach_record(
    db: Session,
    company: RobotCompany,
    *,
    to_emails: list[str],
    subject: str,
    body: str,
    template_type: str,
    status: str,
    is_test: bool = False,
    send_result: Optional[dict[str, Any]] = None,
    payload: Optional[dict[str, Any]] = None,
) -> SupplyOutreachMessage:
    now = datetime.now(timezone.utc)
    reply_token = secrets.token_urlsafe(18)
    msg = SupplyOutreachMessage(
        id=_uuid_for_session(db),
        robot_company_id=company.id,
        to_emails=to_emails,
        from_email=(send_result or {}).get("from_email"),
        reply_to=_supply_reply_address(reply_token),
        reply_token=reply_token,
        subject=subject,
        body_text=body,
        template_type=(template_type or "supply_pipeline").strip() or "supply_pipeline",
        resend_id=(send_result or {}).get("resend_id"),
        status=status,
        is_test=is_test,
        payload=payload or {},
        approved_at=now if status in {"draft_approved", "test_sent", "sent"} else None,
        sent_at=now if status in {"test_sent", "sent"} else None,
    )
    db.add(msg)
    return msg


def _create_crm_supply_tracking_copy(
    db: Session,
    company: RobotCompany,
    *,
    user: dict[str, Any],
    to_emails: list[str],
    subject: str,
    body: str,
    reply_to: str,
    send_result: dict[str, Any],
    supply_message: SupplyOutreachMessage,
) -> tuple[CrmAccount, OutreachMessage]:
    uid = _uid_uuid(user)
    team = _ensure_default_team(db, uid, user.get("email") or "")
    account = (
        db.query(CrmAccount)
        .filter(CrmAccount.team_id == team.id, CrmAccount.name == company.company_name)
        .first()
    )
    if not account:
        account = CrmAccount(
            team_id=team.id,
            name=company.company_name,
            website=company.website,
            industry=company.target_market,
            owner_user_id=uid,
        )
        db.add(account)
        db.flush()
    now = datetime.now(timezone.utc)
    primary_to = to_emails[0]
    account.website = account.website or company.website
    account.industry = account.industry or company.target_market
    account.owner_user_id = account.owner_user_id or uid
    account.contact_email = primary_to
    account.outreach_draft = body
    account.outreach_sent_at = now
    account.outreach_stage = "supply_outreach_sent"
    message = OutreachMessage(
        id=_uuid_for_session(db),
        team_id=_uuid_for_json_uuid_column(db, team.id),
        crm_account_id=_uuid_for_json_uuid_column(db, account.id),
        company_id=None,
        sender_user_id=_uuid_for_json_uuid_column(db, uid),
        to_email=primary_to,
        from_email=send_result.get("from_email"),
        reply_to=reply_to,
        reply_token=secrets.token_urlsafe(18),
        subject=subject,
        body_text=body,
        send_identity="scout",
        resend_id=send_result.get("resend_id"),
        status="sent",
        payload={
            "source": "supply_pipeline",
            "supply_outreach_message_id": str(supply_message.id),
            "robot_company_id": company.id,
            "robot_company_name": company.company_name,
            "all_recipients": to_emails,
            "checkpoint": "Supply outreach sent and copied to CRM.",
        },
        sent_at=now,
    )
    db.add(message)
    record_sales_experience(
        db,
        event_type="supply_outreach_sent",
        outcome="sent",
        team_id=team.id,
        user_id=uid,
        crm_account_id=account.id,
        robot_company_id=company.id,
        channel="email",
        confidence=0.82,
        payload={
            "supply_outreach_message_id": str(supply_message.id),
            "crm_outreach_message_id": str(message.id),
            "all_recipients": to_emails,
        },
    )
    return account, message


def _uuid_for_session(db: Session):
    value = uuid.uuid4()
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return str(value)
    return value


def _uuid_for_json_uuid_column(db: Session, value: Any):
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return str(value) if value is not None else None
    return value


def _recommended_response_playbook(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "Recommended timing: reply within 1 business day once your team signs up.\nSuggested next step: ask Ready For Robots to route the first qualified buyer opportunity and confirm your preferred territory."
    lead_lines = "\n".join(
        f"- {m['company_name']}: respond within 1 business day; propose a 20-minute qualification call; ask about timeline, site count, budget owner, and pilot requirements."
        for m in matches[:3]
    )
    return f"""Suggested timing and next steps for your sales team:
{lead_lines}

Preformatted response sequence:
1. Same day: acknowledge the opportunity and ask Ready For Robots for buyer context, buying timeline, and preferred introduction path.
2. Within 24 hours: send the buyer a short qualification note with two meeting windows and one relevant customer/use-case proof point.
3. Within 3 business days: if there is no response, follow up with a pilot-oriented question and ask whether procurement, operations, or facilities should be included."""


def _vendor_signup_email(rc: RobotCompany, matches: list[dict[str, Any]]) -> dict[str, str]:
    subject = f"3 buyer leads for {rc.company_name}"
    lead_lines = "\n".join(
        f"- {m['company_name']} ({m.get('industry') or 'industry unknown'}): {m.get('why_match')}"
        for m in matches[:3]
    ) or "- We have buyer matches ready to review once your team is onboarded."
    response_playbook = _recommended_response_playbook(matches)
    body = f"""Hello {rc.company_name} team,

I am Cal, and I am reaching out on behalf of Ready For Robots.

We are building a two-sided robot automation marketplace: buyers with live automation signals on one side, and robot companies that can serve those opportunities on the other.

I noticed {rc.company_name} appears to match these buyer opportunities:

{lead_lines}

I am only showing three matches in this note, but the full workflow can deliver qualified leads directly to your inbox with context, timing, and why each buyer appears ready for outreach.

{response_playbook}

The next step is to create a Ready For Robots account so your team can receive lead matches, review the buyer context, and decide which opportunities to pursue.

Would you be open to a short call this week so we can show you the lead flow and confirm the right markets for {rc.company_name}?

Best,
Cal @ Robot Automation Team
Ready For Robots"""
    return {"subject": subject, "body": body}


def _supply_agent_row(db: Session, rc: RobotCompany, *, research_contacts: bool = True) -> dict[str, Any]:
    matches = _match_buyer_leads(db, rc, limit=3)
    research = _research_robot_company_contacts(rc, enabled=research_contacts)
    contact = _contact_strategy(rc, research)
    draft = _vendor_signup_email(rc, matches)
    enriched = _enrich_robot_company(rc)
    history = _supply_outreach_history(db, rc.id)
    return {
        "robot_company": enriched,
        "contact_strategy": contact,
        "contact_research": research,
        "outreach_history": history,
        "lead_matches": matches,
        "email": draft,
        "cta": {
            "signup": "Create a Ready For Robots account to receive matched leads in your inbox.",
            "meeting": "Set up a short call with Ready For Robots to tune target markets and lead delivery.",
        },
        "review_required": True,
    }


def _supply_outreach_history(db: Session, robot_company_id: int, limit: int = 5) -> list[dict[str, Any]]:
    rows = (
        db.query(SupplyOutreachMessage)
        .filter(SupplyOutreachMessage.robot_company_id == robot_company_id)
        .order_by(SupplyOutreachMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(row.id),
            "status": row.status,
            "is_test": bool(row.is_test),
            "to_emails": row.to_emails or [],
            "subject": row.subject,
            "reply_to": row.reply_to,
            "resend_id": row.resend_id,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def _enrich_robot_company(c: RobotCompany) -> dict[str, Any]:
    """JSON-serializable dict with computed vendor_list_score for UI sorting."""
    d = jsonable_encoder(c)
    d.update(compute_vendor_list_score(c))
    return d


@router.get("/")
def get_robot_companies(
    skip: int = 0,
    limit: int = 50,
    country: Optional[str] = None,
    robot_type: Optional[str] = None,
    us_presence: Optional[str] = None,
    priority_tier: Optional[str] = None,
    market_entry_wave: Optional[str] = None,
    distributor_needed: Optional[str] = None,
    min_score: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get robot companies with filtering
    
    Filters:
    - country: China, US, EU, Korea, Japan
    - robot_type: industrial, AMR, cobot, humanoid, service, vision
    - us_presence: office, distributor, none
    - priority_tier: hot, warm, cold
    - market_entry_wave: wave_1, wave_2, wave_3
    - distributor_needed: yes, maybe, no
    - min_score: minimum lead score (0-100)
    - search: company name search
    """
    query = db.query(RobotCompany)
    
    if country:
        query = query.filter(RobotCompany.country == country)
    
    if robot_type:
        query = query.filter(RobotCompany.robot_type == robot_type)
    
    if us_presence:
        query = query.filter(RobotCompany.us_presence == us_presence)
    
    if priority_tier:
        query = query.filter(RobotCompany.priority_tier == priority_tier)
    
    if market_entry_wave:
        query = query.filter(RobotCompany.market_entry_wave == market_entry_wave)
    
    if distributor_needed:
        query = query.filter(RobotCompany.distributor_needed == distributor_needed)
    
    if min_score > 0:
        query = query.filter(RobotCompany.lead_score >= min_score)
    
    if search:
        query = query.filter(RobotCompany.company_name.ilike(f"%{search}%"))
    
    # Order by lead score descending (count before pagination)
    query = query.order_by(RobotCompany.lead_score.desc())
    total = query.count()
    companies = query.offset(skip).limit(limit).all()

    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/hot-leads")
def get_hot_leads(
    min_score: int = 80,
    db: Session = Depends(get_db)
):
    """Get HOT priority leads (score >= 80) ready for outreach"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.priority_tier == "hot",
        RobotCompany.lead_score >= min_score
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "hot_leads": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
    }


@router.get("/chinese-companies")
def get_chinese_companies(
    us_presence: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get Chinese robotics companies
    Filter by U.S. presence: none (needs distribution), distributor (has some), office (established)
    """
    query = db.query(RobotCompany).filter(RobotCompany.country == "China")
    
    if us_presence:
        query = query.filter(RobotCompany.us_presence == us_presence)
    
    companies = query.order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "total": len(companies),
        "filter": us_presence or "all",
    }


@router.get("/market-entry-waves")
def get_market_entry_waves(db: Session = Depends(get_db)):
    """
    Get companies grouped by market entry wave
    Wave 1: 2020-2024 (established)
    Wave 2: 2024-2026 (expanding)
    Wave 3: 2025-2027 (emerging)
    """
    wave_1 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_1"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    wave_2 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_2"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    wave_3 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_3"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "wave_1": {
            "companies": [_enrich_robot_company(c) for c in wave_1],
            "count": len(wave_1),
            "description": "Already Entered U.S. (2020-2024)",
        },
        "wave_2": {
            "companies": [_enrich_robot_company(c) for c in wave_2],
            "count": len(wave_2),
            "description": "Rapid Expansion (2024-2026)",
        },
        "wave_3": {
            "companies": [_enrich_robot_company(c) for c in wave_3],
            "count": len(wave_3),
            "description": "Next-Generation AI Robots (2025-2027)",
        },
    }


@router.get("/needs-distribution")
def get_needs_distribution(db: Session = Depends(get_db)):
    """Get companies that explicitly need U.S. distribution"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.distributor_needed == "yes"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
        "message": "Companies actively seeking U.S. distribution partners",
    }


@router.get("/by-robot-type")
def get_by_robot_type(db: Session = Depends(get_db)):
    """Get companies grouped by robot type"""
    types = ["industrial", "cobot", "AMR", "humanoid", "service", "vision"]
    
    result = {}
    for robot_type in types:
        companies = db.query(RobotCompany).filter(
            RobotCompany.robot_type == robot_type
        ).order_by(RobotCompany.lead_score.desc()).all()
        
        result[robot_type] = {
            "companies": [_enrich_robot_company(c) for c in companies],
            "count": len(companies),
        }
    
    return result


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    total = db.query(RobotCompany).count()
    
    chinese_companies = db.query(RobotCompany).filter(
        RobotCompany.country == "China"
    ).count()
    
    needs_distribution = db.query(RobotCompany).filter(
        RobotCompany.distributor_needed == "yes"
    ).count()
    
    hot_leads = db.query(RobotCompany).filter(
        RobotCompany.priority_tier == "hot"
    ).count()
    
    no_us_presence = db.query(RobotCompany).filter(
        RobotCompany.us_presence == "none"
    ).count()
    
    return {
        "total_companies": total,
        "chinese_companies": chinese_companies,
        "needs_distribution": needs_distribution,
        "hot_leads": hot_leads,
        "no_us_presence": no_us_presence,
        "opportunity": f"{no_us_presence} companies with NO U.S. presence need market entry support"
    }


@router.get("/{company_id}")
def get_robot_company(company_id: int, db: Session = Depends(get_db)):
    """Get single robot company by ID"""
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return _enrich_robot_company(company)


@router.put("/{company_id}/outreach")
def update_outreach_status(
    company_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update outreach status
    Status: not_contacted, contacted, responded, meeting_scheduled, partnership
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.outreach_status = status
    company.last_contact_date = datetime.now()
    
    if notes:
        if company.outreach_notes:
            company.outreach_notes += f"\n\n[{datetime.now().strftime('%Y-%m-%d')}] {notes}"
        else:
            company.outreach_notes = f"[{datetime.now().strftime('%Y-%m-%d')}] {notes}"
    
    db.commit()
    db.refresh(company)

    return _enrich_robot_company(company)


@router.get("/search/by-trade-show")
def search_by_trade_show(
    trade_show: str = Query(..., description="Automate, ProMat, CES, Hannover"),
    db: Session = Depends(get_db)
):
    """Find companies attending specific trade shows"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.trade_shows.contains([trade_show])
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "trade_show": trade_show,
        "companies": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
    }


@router.post("/")
def create_robot_company(company_data: dict, db: Session = Depends(get_db)):
    """Create new robot company lead"""
    company = RobotCompany(**company_data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return _enrich_robot_company(company)


@router.put("/{company_id}")
def update_robot_company(
    company_id: int,
    company_data: dict,
    db: Session = Depends(get_db)
):
    """Update robot company"""
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    for key, value in company_data.items():
        setattr(company, key, value)
    
    db.commit()
    db.refresh(company)

    return _enrich_robot_company(company)


@router.put("/{company_id}/workflow")
def update_workflow(
    company_id: int,
    workflow_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update workflow next steps for a company
    Body: {
        "workflow_stage": "demo|outreach|proposal|negotiation|partnership",
        "next_action": "Schedule product demo",
        "next_action_date": "2026-03-15",
        "assigned_to": "Sales Team",
        "workflow_notes": "CEO interested in AMR solutions",
        "blockers": null
    }
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update workflow fields
    if "workflow_stage" in workflow_data:
        old_stage = company.workflow_stage
        company.workflow_stage = workflow_data["workflow_stage"]
        
        # Log to history
        history = company.workflow_history or []
        history.append({
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "stage": workflow_data["workflow_stage"],
            "previous_stage": old_stage,
            "action": workflow_data.get("next_action", "Stage updated")
        })
        company.workflow_history = history
    
    if "next_action" in workflow_data:
        company.next_action = workflow_data["next_action"]
    if "next_action_date" in workflow_data:
        company.next_action_date = datetime.fromisoformat(workflow_data["next_action_date"])
    if "assigned_to" in workflow_data:
        company.assigned_to = workflow_data["assigned_to"]
    if "workflow_notes" in workflow_data:
        # Append to running log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        existing = company.workflow_notes or ""
        company.workflow_notes = f"{existing}\n[{timestamp}] {workflow_data['workflow_notes']}".strip()
    if "blockers" in workflow_data:
        company.blockers = workflow_data["blockers"]
    
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Workflow updated",
        "company": company.company_name,
        "workflow_stage": company.workflow_stage,
        "next_action": company.next_action,
        "next_action_date": str(company.next_action_date) if company.next_action_date else None
    }


@router.get("/workflow/upcoming")
def get_upcoming_actions(days: int = 7, db: Session = Depends(get_db)):
    """
    Get companies with upcoming next actions in the next N days
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now() + timedelta(days=days)
    
    companies = db.query(RobotCompany).filter(
        RobotCompany.next_action_date <= cutoff_date,
        RobotCompany.next_action_date >= datetime.now()
    ).order_by(RobotCompany.next_action_date).all()
    
    return {
        "upcoming_actions": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "workflow_stage": c.workflow_stage,
                "next_action": c.next_action,
                "next_action_date": str(c.next_action_date),
                "assigned_to": c.assigned_to,
                "priority_tier": c.priority_tier,
                "lead_score": c.lead_score,
                "blockers": c.blockers
            }
            for c in companies
        ],
        "count": len(companies),
        "days": days
    }


@router.get("/agent/supply-side")
def supply_side_agent(
    limit: int = Query(10, ge=1, le=50),
    min_score: int = Query(0, ge=0, le=100),
    search: Optional[str] = None,
    research_contacts: bool = Query(True, description="Run bounded official-site contact research"),
    research_limit: int = Query(4, ge=0, le=10, description="Maximum rows to live-research per request"),
    db: Session = Depends(get_db),
):
    """
    Research robot companies, identify who to contact, match up to 3 buyer leads,
    and draft signup/meeting outreach for review.
    """
    query = db.query(RobotCompany)
    if min_score:
        query = query.filter(RobotCompany.lead_score >= min_score)
    if search:
        query = query.filter(RobotCompany.company_name.ilike(f"%{search}%"))
    companies = query.order_by(RobotCompany.lead_score.desc(), RobotCompany.updated_at.desc().nullslast()).limit(limit).all()
    rows = [
        _supply_agent_row(db, rc, research_contacts=research_contacts and index < research_limit)
        for index, rc in enumerate(companies)
    ]
    return {
        "agent": "robot_company_supply_pipeline",
        "review_required": True,
        "instructions": "Review contact strategy and drafted email before sending. Each email shows only 3 buyer matches.",
        "companies": rows,
        "count": len(rows),
    }


@router.post("/{company_id}/email/approve")
def approve_supply_outreach(
    company_id: int,
    payload: ApproveSupplyOutreachRequest,
    db: Session = Depends(get_db),
):
    """
    Persist an operator-approved supply-side draft before any live send.
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    to_emails, subject, body = _require_supply_outreach_payload(payload)
    msg = _create_supply_outreach_record(
        db,
        company,
        to_emails=to_emails,
        subject=subject,
        body=body,
        template_type=payload.template_type,
        status="draft_approved",
        payload=payload.payload,
    )
    company.workflow_stage = company.workflow_stage or "outreach"
    company.next_action = "Send approved Ready For Robots supply outreach"
    db.commit()
    db.refresh(msg)
    return {
        "approved": True,
        "supply_outreach_message_id": str(msg.id),
        "status": msg.status,
        "to_email": msg.to_emails,
        "approved_at": msg.approved_at.isoformat() if msg.approved_at else None,
        "reply_to": msg.reply_to,
    }


@router.get("/{company_id}/email")
def generate_email(
    company_id: int,
    template_type: str = Query("intro", description="intro, demo, proposal, followup, trade_show, hot_lead"),
    db: Session = Depends(get_db)
):
    """
    Generate personalized email for company outreach
    
    Template types:
    - intro: Initial introduction email
    - demo: Request product demonstration
    - proposal: Partnership proposal after demo
    - followup: Follow-up for non-responsive leads
    - trade_show: Trade show meeting invitation
    - hot_lead: High-priority outreach for hot leads
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Convert company to dict for template
    company_data = {
        'company_name': company.company_name,
        'robot_type': company.robot_type,
        'target_market': company.target_market,
        'us_presence': company.us_presence,
        'lead_score': company.lead_score,
        'unique_selling_points': company.unique_selling_points or [],
        'website': company.website
    }
    
    # Use workflow_stage if template_type is 'auto'
    if template_type == 'auto':
        template_type = company.workflow_stage or 'intro'
    
    email = get_email_template(template_type, company_data)
    
    return {
        "company_id": company_id,
        "company_name": company.company_name,
        "template_type": template_type,
        "email": email
    }


@router.post("/{company_id}/email/log")
def log_email_sent(
    company_id: int,
    email_data: dict,
    db: Session = Depends(get_db)
):
    """
    Log that an email was sent to a company
    Updates workflow notes and last contact date
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update last contact date
    company.last_contact_date = datetime.now()
    
    # Log to workflow notes
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    template_type = email_data.get('template_type', 'email')
    subject = email_data.get('subject', 'Email sent')
    
    existing = company.workflow_notes or ""
    company.workflow_notes = f"{existing}\n[{timestamp}] Sent {template_type} email: {subject}".strip()
    
    # Update outreach status if not contacted yet
    if company.outreach_status == 'not_contacted':
        company.outreach_status = 'contacted'
    
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Email logged successfully",
        "company": company.company_name,
        "last_contact_date": str(company.last_contact_date)
    }


@router.post("/{company_id}/email/send")
def send_email(
    company_id: int,
    payload: SendRobotCompanyEmailRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    """
    Send outreach email via Resend and log activity.
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_data = {
        "company_name": company.company_name,
        "robot_type": company.robot_type,
        "target_market": company.target_market,
        "us_presence": company.us_presence,
        "lead_score": company.lead_score,
        "unique_selling_points": company.unique_selling_points or [],
        "website": company.website,
    }
    template_type = (payload.template_type or "intro").strip() or "intro"
    email = get_email_template(template_type, company_data)
    subject = payload.subject or email.get("subject", "Partnership Opportunity")
    body = payload.body or email.get("body", "")
    to_emails = _request_emails(payload.to_email)
    if not to_emails:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")
    reply_token = secrets.token_urlsafe(18)
    reply_to = _supply_reply_address(reply_token)

    try:
        send_result = send_email_via_resend(
            to_email=to_emails,
            subject=subject,
            body_text=body,
            from_display_name="Cal",
            reply_to=reply_to,
            idempotency_key=f"supply-outreach/{company.id}/{'-'.join(to_emails)[:120]}",
        )
    except ResendEmailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    msg = SupplyOutreachMessage(
        id=_uuid_for_session(db),
        robot_company_id=company.id,
        to_emails=to_emails,
        from_email=send_result.get("from_email"),
        reply_to=reply_to,
        reply_token=reply_token,
        subject=subject,
        body_text=body,
        template_type=template_type,
        resend_id=send_result.get("resend_id"),
        status="sent",
        is_test=False,
        payload={"source": "supply_pipeline"},
        approved_at=datetime.now(timezone.utc),
        sent_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    crm_account, crm_message = _create_crm_supply_tracking_copy(
        db,
        company,
        user=user,
        to_emails=to_emails,
        subject=subject,
        body=body,
        reply_to=reply_to,
        send_result=send_result,
        supply_message=msg,
    )
    company.last_contact_date = datetime.now(timezone.utc)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    existing = company.workflow_notes or ""
    company.workflow_notes = (
        f"{existing}\n[{timestamp}] Sent {template_type} email to {send_result.get('to') or to_emails}: {subject}"
    ).strip()
    if company.outreach_status == "not_contacted":
        company.outreach_status = "contacted"

    db.commit()
    db.refresh(company)
    db.refresh(msg)
    db.refresh(crm_account)
    db.refresh(crm_message)

    return {
        "message": "Email sent via Resend",
        "company": company.company_name,
        "to_email": send_result.get("to") or to_emails,
        "template_type": template_type,
        "subject": subject,
        "supply_outreach_message_id": str(msg.id),
        "status": msg.status,
        "resend_id": send_result.get("resend_id"),
        "from_email": send_result.get("from_email"),
        "reply_to": reply_to,
        "crm_account_id": str(crm_account.id),
        "crm_outreach_message_id": str(crm_message.id),
        "workflow_checkpoint": "Sent checkpoint recorded and copied to CRM.",
        "last_contact_date": str(company.last_contact_date),
    }


@router.post("/{company_id}/email/test-send")
def test_send_email(
    company_id: int,
    payload: SendRobotCompanyEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Send a test outreach email via Resend without mutating workflow state.
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_data = {
        "company_name": company.company_name,
        "robot_type": company.robot_type,
        "target_market": company.target_market,
        "us_presence": company.us_presence,
        "lead_score": company.lead_score,
        "unique_selling_points": company.unique_selling_points or [],
        "website": company.website,
    }
    template_type = (payload.template_type or "intro").strip() or "intro"
    email = get_email_template(template_type, company_data)
    raw_subject = payload.subject or email.get("subject", "Partnership Opportunity")
    subject = f"[TEST] {raw_subject}"
    body = payload.body or email.get("body", "")
    to_emails = _request_emails(payload.to_email)
    if not to_emails:
        raise HTTPException(status_code=400, detail="At least one recipient email is required")

    try:
        send_result = send_email_via_resend(
            to_email=to_emails,
            subject=subject,
            body_text=body,
            from_display_name="Cal",
            idempotency_key=f"supply-outreach-test/{company.id}/{'-'.join(to_emails)[:120]}",
        )
    except ResendEmailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    msg = _create_supply_outreach_record(
        db,
        company,
        to_emails=to_emails,
        subject=subject,
        body=body,
        template_type=template_type,
        status="test_sent",
        is_test=True,
        send_result=send_result,
        payload={"source": "supply_pipeline_test"},
    )
    db.commit()
    db.refresh(msg)

    return {
        "message": "Test email sent via Resend",
        "company": company.company_name,
        "to_email": send_result.get("to") or to_emails,
        "template_type": template_type,
        "subject": subject,
        "supply_outreach_message_id": str(msg.id),
        "status": msg.status,
        "resend_id": send_result.get("resend_id"),
        "from_email": send_result.get("from_email"),
        "reply_to": msg.reply_to,
    }


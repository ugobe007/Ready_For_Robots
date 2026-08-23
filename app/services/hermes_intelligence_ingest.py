"""Hermes → RFR intelligence ingest helpers (jobs, qualify, contacts, vendor news)."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_CONTACT_CONFIDENCE_FLOOR = 40
_NEWS_TYPES = frozenset(
    {"capability", "pricing", "foundation_model", "product", "customer_signal"}
)


def _sha_id(prefix: str, *parts: str) -> str:
    blob = "|".join((p or "").strip().lower() for p in parts)
    return f"{prefix}-{hashlib.sha1(blob.encode('utf-8')).hexdigest()[:12]}"


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


def _split_location(location: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not location:
        return None, None, None
    parts = [p.strip() for p in location.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 1:
        return parts[0], None, None
    return None, None, None


def find_or_create_company(
    db,
    *,
    employer: str,
    website: Optional[str] = None,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    source: str = "hermes_job_orders",
) -> Any:
    from app.models.company import Company

    name = _norm_name(employer)
    if not name:
        raise ValueError("employer name required")

    domain = None
    if website:
        try:
            from app.services.company_domain import normalize_website_domain

            domain = normalize_website_domain(website)
        except Exception:
            domain = None

    row = None
    if domain:
        row = db.query(Company).filter(Company.website_domain == domain).first()
    if row is None:
        row = (
            db.query(Company)
            .filter(Company.name.ilike(name))
            .order_by(Company.id.asc())
            .first()
        )
    city, state, country = _split_location(location)
    if row is None:
        row = Company(
            name=name,
            website=website,
            industry=industry,
            location_city=city,
            location_state=state,
            location_country=country,
            source=source,
            is_internal=True,
            crm_metadata={},
        )
        db.add(row)
        db.flush()
    else:
        if website and not row.website:
            row.website = website
        if industry and not row.industry:
            row.industry = industry
        if city and not row.location_city:
            row.location_city = city
        if state and not row.location_state:
            row.location_state = state
        if country and not row.location_country:
            row.location_country = country
    return row


def ingest_job_signal(
    db,
    *,
    job_title: str,
    employer: str,
    excerpt: str,
    source_url: Optional[str] = None,
    location: Optional[str] = None,
    source_date: Optional[str] = None,
    industry: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create/update Company + Signal and reconstruct a WORK unit."""
    from app.models.signal import Signal
    from app.services.work_unit_reconstruct import reconstruct_work_from_text, work_unit_summary
    from app.services.work_unit_store import upsert_work_unit

    title = (job_title or "").strip()
    text = (excerpt or "").strip()
    if len(text) < 20:
        raise ValueError("excerpt must be at least 20 characters")
    if not title:
        raise ValueError("job_title required")

    work = reconstruct_work_from_text(text, job_title=title, source_id=source_url)
    summary = work_unit_summary(work)
    preview = {
        "employer": _norm_name(employer),
        "job_title": title,
        "source_url": source_url,
        "source_date": source_date,
        "location": location,
        "work": summary,
    }
    if dry_run:
        return {"dry_run": True, **preview}

    company = find_or_create_company(
        db,
        employer=employer,
        website=None,
        location=location,
        industry=industry,
        source="hermes_job_orders",
    )
    # Dedup by source_url when present
    signal = None
    if source_url:
        signal = (
            db.query(Signal)
            .filter(Signal.company_id == company.id, Signal.source_url == source_url)
            .first()
        )
    signal_text = f"{title}\n\n{text}"[:4000]
    if signal is None:
        signal = Signal(
            company_id=company.id,
            signal_type="hermes_job_order",
            signal_text=signal_text,
            ingestion_raw_text=text[:8000],
            signal_strength=float(summary.get("confidence") or 0.55),
            source_url=source_url,
        )
        db.add(signal)
        db.flush()
    else:
        signal.signal_text = signal_text
        signal.ingestion_raw_text = text[:8000]
        signal.signal_strength = float(summary.get("confidence") or signal.signal_strength or 0.55)

    meta = dict(company.crm_metadata or {})
    hermes_jobs = list(meta.get("hermes_job_orders") or [])
    hermes_jobs.append(
        {
            "signal_id": signal.id,
            "job_title": title,
            "source_url": source_url,
            "source_date": source_date,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    meta["hermes_job_orders"] = hermes_jobs[-20:]
    company.crm_metadata = meta

    wu_row = upsert_work_unit(
        db,
        company_id=company.id,
        work=summary,
        raw_excerpt=text[:2000],
    )
    db.flush()
    return {
        "dry_run": False,
        "company_id": company.id,
        "company_name": company.name,
        "signal_id": signal.id,
        "work_unit_id": summary.get("work_unit_id"),
        "work_unit_pk": str(wu_row.id) if wu_row is not None else None,
        "workflow_family": summary.get("workflow_family"),
        "confidence": summary.get("confidence"),
        **preview,
    }


def apply_qualify_overlay(
    db,
    *,
    company_id: Optional[int] = None,
    signal_url: Optional[str] = None,
    automation_fit: int,
    labor_intensity: Optional[str] = None,
    facility_clarity: Optional[str] = None,
    blockers: Optional[list[str]] = None,
    rationale: Optional[str] = None,
    vendor_shortlist: Optional[list[dict[str, Any]]] = None,
    hermes_run_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Persist Hermes qualification overlay on company.crm_metadata (not CRM truth)."""
    from app.models.company import Company
    from app.models.signal import Signal

    if automation_fit < 0 or automation_fit > 100:
        raise ValueError("automation_fit must be 0–100")

    overlay = {
        "automation_fit": int(automation_fit),
        "labor_intensity": labor_intensity,
        "facility_clarity": facility_clarity,
        "blockers": list(blockers or []),
        "rationale": (rationale or "")[:2000],
        "vendor_shortlist": list(vendor_shortlist or [])[:8],
        "hermes_run_id": hermes_run_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "truth_state": "HERMES_OVERLAY",  # not customer-confirmed QUALIFY
    }
    if dry_run:
        return {
            "dry_run": True,
            "company_id": company_id,
            "hermes_qualify": overlay,
        }

    company = None
    if company_id is not None:
        company = db.query(Company).filter(Company.id == int(company_id)).first()
    elif signal_url:
        sig = db.query(Signal).filter(Signal.source_url == signal_url).first()
        if sig:
            company = db.query(Company).filter(Company.id == sig.company_id).first()
    if company is None:
        raise ValueError("company not found for company_id or signal_url")

    meta = dict(company.crm_metadata or {})
    meta["hermes_qualify"] = overlay
    company.crm_metadata = meta
    db.flush()
    return {
        "dry_run": False,
        "company_id": company.id,
        "company_name": company.name,
        "hermes_qualify": overlay,
    }


def ingest_contact(
    db,
    *,
    company_id: int,
    name: str,
    title: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    email: Optional[str] = None,
    source_url: Optional[str] = None,
    confidence: int = 50,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Upsert a public-sourced Contact. Never invent emails — caller must supply only public ones."""
    from app.models.company import Company
    from app.models.contact import Contact

    conf = int(confidence)
    if conf < _CONTACT_CONFIDENCE_FLOOR:
        return {
            "skipped": True,
            "reason": f"confidence {conf} below floor {_CONTACT_CONFIDENCE_FLOOR}",
            "company_id": company_id,
            "name": name,
        }

    parts = _norm_name(name).split(" ", 1)
    first = parts[0] if parts else name
    last = parts[1] if len(parts) > 1 else None
    preview = {
        "company_id": company_id,
        "first_name": first,
        "last_name": last,
        "title": title,
        "linkedin_url": linkedin_url,
        "email": email,
        "confidence_score": conf,
        "source_url": source_url,
    }
    if dry_run:
        return {"dry_run": True, **preview}

    company = db.query(Company).filter(Company.id == int(company_id)).first()
    if company is None:
        raise ValueError(f"company_id {company_id} not found")

    row = None
    if linkedin_url:
        row = (
            db.query(Contact)
            .filter(Contact.company_id == company_id, Contact.linkedin_url == linkedin_url)
            .first()
        )
    if row is None and email:
        row = (
            db.query(Contact)
            .filter(Contact.company_id == company_id, Contact.email == email)
            .first()
        )
    if row is None:
        row = (
            db.query(Contact)
            .filter(
                Contact.company_id == company_id,
                Contact.first_name.ilike(first),
                Contact.last_name.ilike(last or ""),
            )
            .first()
        )
    if row is None:
        row = Contact(company_id=company_id, first_name=first, last_name=last)
        db.add(row)

    row.title = title or row.title
    row.linkedin_url = linkedin_url or row.linkedin_url
    if email:
        row.email = email
    row.confidence_score = max(int(row.confidence_score or 0), conf)

    meta = dict(company.crm_metadata or {})
    dms = list(meta.get("hermes_decision_makers") or [])
    dms.append(
        {
            "name": _norm_name(name),
            "title": title,
            "source_url": source_url,
            "confidence": conf,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    meta["hermes_decision_makers"] = dms[-30:]
    company.crm_metadata = meta
    db.flush()
    return {
        "dry_run": False,
        "contact_id": row.id,
        "company_id": company_id,
        "company_name": company.name,
        **preview,
    }


def ingest_vendor_news(
    db,
    *,
    entity_name: str,
    text: str,
    news_type: str = "product",
    entity_kind: str = "vendor",
    source_url: Optional[str] = None,
    source_date: Optional[str] = None,
    title: Optional[str] = None,
    company_id: Optional[int] = None,
    confidence: float = 0.5,
    hermes_run_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    from app.models.vendor_news import VendorNewsItem

    nt = (news_type or "product").strip().lower()
    if nt not in _NEWS_TYPES:
        raise ValueError(f"news_type must be one of {sorted(_NEWS_TYPES)}")
    ek = (entity_kind or "vendor").strip().lower()
    if ek not in {"vendor", "customer"}:
        raise ValueError("entity_kind must be vendor or customer")
    body = (text or "").strip()
    if len(body) < 20:
        raise ValueError("text must be at least 20 characters")
    name = _norm_name(entity_name)
    if not name:
        raise ValueError("entity_name required")

    news_id = _sha_id("VN", ek, name, source_url or "", body[:120])
    preview = {
        "news_id": news_id,
        "news_type": nt,
        "entity_kind": ek,
        "entity_name": name,
        "source_url": source_url,
        "source_date": source_date,
        "title": title,
        "company_id": company_id,
        "confidence": float(confidence),
    }
    if dry_run:
        return {"dry_run": True, **preview}

    # Link customer news to company by name when company_id omitted
    if company_id is None and ek == "customer":
        try:
            company = find_or_create_company(
                db, employer=name, source="hermes_vendor_customer_news"
            )
            company_id = company.id
        except Exception:
            company_id = None

    row = db.query(VendorNewsItem).filter(VendorNewsItem.news_id == news_id).one_or_none()
    if row is None and source_url:
        row = (
            db.query(VendorNewsItem)
            .filter(VendorNewsItem.source_url == source_url)
            .first()
        )
    if row is None:
        row = VendorNewsItem(news_id=news_id, text=body)
        db.add(row)

    row.news_type = nt
    row.entity_kind = ek
    row.entity_name = name
    row.company_id = company_id
    row.title = title
    row.text = body[:8000]
    row.source_url = source_url
    row.source_date = source_date
    row.confidence = float(confidence)
    row.hermes_run_id = hermes_run_id
    row.extra = {
        "domain": (urlparse(source_url).netloc if source_url else None),
    }
    db.flush()
    return {
        "dry_run": False,
        "db_id": str(row.id),
        **preview,
        "company_id": company_id,
    }


def apply_buying_window_overlay(
    db,
    *,
    company_id: int,
    urgency_0_100: int,
    window_label: Optional[str] = None,
    factors: Optional[list[dict[str, Any]]] = None,
    cal_hint: Optional[str] = None,
    confidence: Optional[float] = None,
    hermes_run_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Persist timing urgency on company.crm_metadata.hermes_buying_window (not automation fit)."""
    from app.models.company import Company

    urgency = int(urgency_0_100)
    if urgency < 0 or urgency > 100:
        raise ValueError("urgency_0_100 must be 0–100")
    overlay = {
        "urgency_0_100": urgency,
        "window_label": (window_label or "")[:160] or None,
        "factors": list(factors or [])[:12],
        "cal_hint": (cal_hint or "")[:280] or None,
        "confidence": None if confidence is None else float(confidence),
        "hermes_run_id": hermes_run_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "truth_state": "HERMES_OVERLAY",
    }
    if dry_run:
        return {
            "dry_run": True,
            "company_id": company_id,
            "hermes_buying_window": overlay,
        }

    company = db.query(Company).filter(Company.id == int(company_id)).first()
    if company is None:
        raise ValueError(f"company_id {company_id} not found")
    meta = dict(company.crm_metadata or {})
    meta["hermes_buying_window"] = overlay
    company.crm_metadata = meta
    db.flush()
    return {
        "dry_run": False,
        "company_id": company.id,
        "company_name": company.name,
        "hermes_buying_window": overlay,
    }


def _video_item(
    *,
    source_url: str,
    platform: Optional[str],
    evidence_kind: Optional[str],
    title: Optional[str],
    excerpt: Optional[str],
    workflow_hint: Optional[str],
    robot_visible: Optional[str],
    facility_hint: Optional[str],
    confidence: Optional[float],
    published_at: Optional[str],
) -> dict[str, Any]:
    url = (source_url or "").strip()
    if not url:
        raise ValueError("source_url required")
    return {
        "source_url": url[:500],
        "platform": (platform or urlparse(url).netloc or "unknown")[:64],
        "evidence_kind": (evidence_kind or "facility_tour")[:64],
        "title": (title or "")[:240] or None,
        "excerpt": (excerpt or "")[:800] or None,
        "workflow_hint": (workflow_hint or "")[:160] or None,
        "robot_visible": (robot_visible or "")[:120] or None,
        "facility_hint": (facility_hint or "")[:160] or None,
        "confidence": None if confidence is None else float(confidence),
        "published_at": published_at,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }


def ingest_video_evidence(
    db,
    *,
    company_id: Optional[int] = None,
    company_name: Optional[str] = None,
    source_url: str,
    platform: Optional[str] = None,
    evidence_kind: Optional[str] = None,
    title: Optional[str] = None,
    excerpt: Optional[str] = None,
    workflow_hint: Optional[str] = None,
    robot_visible: Optional[str] = None,
    facility_hint: Optional[str] = None,
    confidence: Optional[float] = None,
    published_at: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append URL-deduped customer use-case video onto crm_metadata.hermes_video_evidence."""
    from app.models.company import Company

    item = _video_item(
        source_url=source_url,
        platform=platform,
        evidence_kind=evidence_kind,
        title=title,
        excerpt=excerpt,
        workflow_hint=workflow_hint,
        robot_visible=robot_visible,
        facility_hint=facility_hint,
        confidence=confidence,
        published_at=published_at,
    )
    if dry_run:
        return {
            "dry_run": True,
            "company_id": company_id,
            "company_name": company_name,
            "hermes_video_evidence": item,
        }

    company = None
    if company_id is not None:
        company = db.query(Company).filter(Company.id == int(company_id)).first()
    elif company_name:
        company = find_or_create_company(
            db, employer=company_name, source="hermes_video_evidence"
        )
    if company is None:
        raise ValueError("company_id or company_name required")

    meta = dict(company.crm_metadata or {})
    videos = [
        v
        for v in list(meta.get("hermes_video_evidence") or [])
        if isinstance(v, dict) and v.get("source_url") != item["source_url"]
    ]
    videos.append(item)
    meta["hermes_video_evidence"] = videos[-25:]
    company.crm_metadata = meta
    db.flush()
    return {
        "dry_run": False,
        "company_id": company.id,
        "company_name": company.name,
        "hermes_video_evidence": item,
        "stored": len(meta["hermes_video_evidence"]),
    }


def ingest_vendor_video_evidence(
    db,
    *,
    vendor_name: str,
    source_url: str,
    platform: Optional[str] = None,
    evidence_kind: Optional[str] = None,
    title: Optional[str] = None,
    robot_model: Optional[str] = None,
    confidence: Optional[float] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append OEM demo / field video onto robot_companies.market_intelligence."""
    from app.models.robot_company import RobotCompany

    name = _norm_name(vendor_name)
    if not name:
        raise ValueError("vendor_name required")
    item = _video_item(
        source_url=source_url,
        platform=platform,
        evidence_kind=evidence_kind or "oem_demo",
        title=title,
        excerpt=None,
        workflow_hint=None,
        robot_visible=robot_model,
        facility_hint=None,
        confidence=confidence,
        published_at=None,
    )
    item["robot_model"] = (robot_model or "")[:120] or None
    if dry_run:
        return {
            "dry_run": True,
            "vendor_name": name,
            "hermes_video_evidence": item,
        }

    row = (
        db.query(RobotCompany)
        .filter(RobotCompany.company_name.ilike(name))
        .order_by(RobotCompany.id.asc())
        .first()
    )
    if row is None:
        raise ValueError(f"robot vendor {name!r} not found")
    intel = dict(row.market_intelligence or {})
    videos = [
        v
        for v in list(intel.get("hermes_video_evidence") or [])
        if isinstance(v, dict) and v.get("source_url") != item["source_url"]
    ]
    videos.append(item)
    intel["hermes_video_evidence"] = videos[-25:]
    row.market_intelligence = intel
    db.flush()
    return {
        "dry_run": False,
        "vendor_name": row.company_name,
        "robot_company_id": row.id,
        "hermes_video_evidence": item,
        "stored": len(intel["hermes_video_evidence"]),
    }


def list_video_seed_targets(
    db,
    *,
    kind: str = "both",
    missing_only: bool = True,
    limit: int = 40,
) -> dict[str, Any]:
    """Companies / vendors still missing Hermes video evidence (for cron seeds)."""
    from app.models.company import Company
    from app.models.robot_company import RobotCompany

    kind_n = (kind or "both").strip().lower()
    cap = max(1, min(int(limit), 80))
    customers: list[dict[str, Any]] = []
    vendors: list[dict[str, Any]] = []
    if kind_n in {"customer", "both"}:
        rows = db.query(Company).order_by(Company.id.desc()).limit(200).all()
        for c in rows:
            meta = c.crm_metadata if isinstance(c.crm_metadata, dict) else {}
            videos = meta.get("hermes_video_evidence") or []
            if missing_only and videos:
                continue
            customers.append(
                {
                    "company_id": c.id,
                    "name": c.name,
                    "has_video": bool(videos),
                    "has_qualify": bool(meta.get("hermes_qualify")),
                }
            )
            if len(customers) >= cap:
                break
    if kind_n in {"vendor", "both"}:
        rows = (
            db.query(RobotCompany)
            .order_by(RobotCompany.id.desc())
            .limit(200)
            .all()
        )
        for r in rows:
            intel = r.market_intelligence if isinstance(r.market_intelligence, dict) else {}
            videos = intel.get("hermes_video_evidence") or []
            if missing_only and videos:
                continue
            vendors.append(
                {
                    "robot_company_id": r.id,
                    "name": r.company_name,
                    "has_video": bool(videos),
                }
            )
            if len(vendors) >= cap:
                break
    return {
        "kind": kind_n,
        "missing_only": missing_only,
        "customers": customers,
        "vendors": vendors,
        "count": len(customers) + len(vendors),
    }

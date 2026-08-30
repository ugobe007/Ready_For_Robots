"""Extract Robot Job fields from a public job posting.

Unknown is valid. Do not invent wages, throughput, or FTE.
Used by job-board scrapers so SIGNAL labor_pain rows become employment objects.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from urllib.parse import urlparse

from app.services.email_address import normalize_recipient_email

# Title fragment → job function (employment family, not a buyer persona).
JOB_FUNCTION_BY_TITLE = (
    ("order picker", "picking"),
    ("case picker", "picking"),
    ("picker", "picking"),
    ("packer", "packing"),
    ("packaging", "packing"),
    ("forklift", "material_handling"),
    ("material handler", "material_handling"),
    ("warehouse associate", "material_handling"),
    ("fulfillment", "material_handling"),
    ("receiving", "receiving"),
    ("shipping", "shipping"),
    ("dock worker", "shipping"),
    ("replenish", "replenishment"),
    ("housekeeper", "housekeeping"),
    ("restroom attendant", "cleaning"),
    ("room attendant", "housekeeping"),
    ("evs", "environmental_services"),
    ("environmental services", "environmental_services"),
    ("floor tech", "environmental_services"),
    ("dishwasher", "warewash"),
    ("line cook", "food_prep"),
    ("prep cook", "food_prep"),
    ("grill cook", "food_prep"),
    ("make line", "food_prep"),
    ("bowl assembl", "food_prep"),
    ("kitchen automation", "food_prep"),
    ("ingredient dos", "food_prep"),
    ("tortilla", "food_prep"),
    ("cook", "food_prep"),
    ("banquet server", "serving"),
    ("food runner", "serving"),
    ("busser", "serving"),
    ("bartender", "serving"),
    ("cocktail", "serving"),
    ("server", "serving"),
    ("janitor", "cleaning"),
    ("custodian", "cleaning"),
    ("floor cleaner", "cleaning"),
    ("warehouse worker", "material_handling"),
    ("night audit", "front_desk"),
    ("front desk", "front_desk"),
    ("houseperson", "housekeeping"),
    ("palletiz", "palletizing"),
    ("patient transporter", "patient_transport"),
    ("patient transport", "patient_transport"),
    ("pharmacy technician", "pharmacy"),
    ("dietary aide", "food_prep"),
    ("laundry", "laundry"),
    ("harvest worker", "harvest"),
    ("farm worker", "field_work"),
    ("farm laborer", "field_work"),
    ("tractor operator", "tractor"),
    ("haul truck", "haulage"),
    ("underground miner", "haulage"),
    ("drywall", "drywall"),
    ("framing carpenter", "framing"),
    ("construction laborer", "construction_labor"),
    ("bricklayer", "construction_labor"),
    ("machine tender", "machine_tending"),
    ("cnc operator", "machine_tending"),
    ("cnc", "machine_tending"),
    ("production line", "machine_tending"),
    ("machine operator", "machine_tending"),
    ("palletizer", "palletizing"),
)

WAGE_HOUR_RE = re.compile(
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:-|–|to)\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:an?\s+hour|/hr|per\s+hour|hourly)",
    re.I,
)
WAGE_HOUR_SINGLE_RE = re.compile(
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:an?\s+hour|/hr|per\s+hour|hourly)",
    re.I,
)
WAGE_YEAR_RE = re.compile(
    r"\$\s*(\d{2,3}(?:,\d{3})+)\s*(?:-|–|to)\s*\$?\s*(\d{2,3}(?:,\d{3})+)\s*(?:a\s+year|per\s+year|annually|/yr)",
    re.I,
)
SIGNING_BONUS_RE = re.compile(
    r"(?:sign(?:ing|-on)|sign on)\s+bonus(?:\s+of)?\s*\$\s*(\d{1,3}(?:,\d{3})*)",
    re.I,
)
THROUGHPUT_RE = re.compile(
    r"(\d{1,4})\s*(cases|totes|pallets|units|rooms|carts)\s*(?:per|/)\s*(hour|hr|shift|night)",
    re.I,
)
PAYLOAD_RE = re.compile(
    r"(?:up to|lift|payload|weigh(?:s|ing)?)\s*(\d{1,5})\s*(lb|lbs|pounds|kg|kilograms)",
    re.I,
)
SHIFT_RE = re.compile(
    r"\b(overnight|3rd shift|third shift|night shift|2nd shift|second shift|1st shift|weekend|graveyard)\b",
    re.I,
)
OPENINGS_RE = re.compile(
    r"(\d{1,3})\s+(?:openings|positions|associates needed|hires)",
    re.I,
)


def _money(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", ""))
    except (TypeError, ValueError):
        return None


_IT_SERVER_TITLE_RE = re.compile(
    r"\b(?:windows|sql|linux|exchange|web|mail|file|proxy|dns|application)\s+server\b|"
    r"\bserver\s+(?:admin|administrator|engineer|developer|operator|rack|room)\b",
    re.I,
)


def job_function_from_title(title: str) -> Optional[str]:
    blob = (title or "").lower()
    if not blob:
        return None
    skip_bare_server = bool(_IT_SERVER_TITLE_RE.search(blob))
    for needle, family in JOB_FUNCTION_BY_TITLE:
        if skip_bare_server and family == "serving" and needle == "server":
            continue
        if needle in blob:
            return family
    return None


def extract_compensation(text: str) -> dict[str, Any]:
    blob = text or ""
    out: dict[str, Any] = {
        "wage_min": None,
        "wage_max": None,
        "wage_unit": None,
        "currency": None,
        "signing_bonus": None,
        "excerpt": None,
    }
    m = WAGE_HOUR_RE.search(blob)
    if m:
        out["wage_min"] = _money(m.group(1))
        out["wage_max"] = _money(m.group(2))
        out["wage_unit"] = "hour"
        out["currency"] = "USD"
        out["excerpt"] = m.group(0).strip()
    else:
        m = WAGE_HOUR_SINGLE_RE.search(blob)
        if m:
            val = _money(m.group(1))
            out["wage_min"] = val
            out["wage_max"] = val
            out["wage_unit"] = "hour"
            out["currency"] = "USD"
            out["excerpt"] = m.group(0).strip()
        else:
            m = WAGE_YEAR_RE.search(blob)
            if m:
                out["wage_min"] = _money(m.group(1))
                out["wage_max"] = _money(m.group(2))
                out["wage_unit"] = "year"
                out["currency"] = "USD"
                out["excerpt"] = m.group(0).strip()
    b = SIGNING_BONUS_RE.search(blob)
    if b:
        out["signing_bonus"] = _money(b.group(1))
        if not out["excerpt"]:
            out["excerpt"] = b.group(0).strip()
    return out


def extract_performance_specs(text: str) -> dict[str, Any]:
    blob = text or ""
    specs: dict[str, Any] = {
        "throughput": None,
        "payload": None,
        "shift": None,
        "openings": None,
    }
    t = THROUGHPUT_RE.search(blob)
    if t:
        specs["throughput"] = {
            "count": int(t.group(1)),
            "unit": t.group(2).lower(),
            "per": t.group(3).lower(),
            "excerpt": t.group(0).strip(),
        }
    p = PAYLOAD_RE.search(blob)
    if p:
        specs["payload"] = {
            "value": int(p.group(1)),
            "unit": "lb" if p.group(2).lower().startswith("lb") or p.group(2).lower() == "pounds" else "kg",
            "excerpt": p.group(0).strip(),
        }
    s = SHIFT_RE.search(blob)
    if s:
        specs["shift"] = s.group(1).lower()
    o = OPENINGS_RE.search(blob)
    if o:
        specs["openings"] = int(o.group(1))
    return specs


def extract_robot_job(
    *,
    title: str,
    description: str = "",
    company: str = "",
    locality: str = "",
    source_url: str = "",
    html: str = "",
    jsonld: Any = None,
) -> dict[str, Any]:
    blob = f"{title or ''}\n{description or ''}"
    function = job_function_from_title(title)
    pay = extract_compensation(blob)
    specs = extract_performance_specs(blob)
    unknowns: list[str] = []
    if not pay["wage_min"]:
        unknowns.append("compensation")
    if not specs["throughput"] and not specs["payload"]:
        unknowns.append("performance_specs")
    if not function:
        unknowns.append("job_function")
    contacts = extract_job_contacts(
        html=html or "",
        jsonld=jsonld,
        description=description or "",
        employer=company,
        title=title,
    )
    return {
        "employer": (company or "").strip() or None,
        "workplace": (locality or "").strip() or None,
        "job_title": (title or "").strip() or None,
        "job_function": function,
        "compensation": pay,
        "performance_specs": specs,
        "source_url": source_url or None,
        "employer_email": contacts.get("employer_email"),
        "contact_url": contacts.get("contact_url"),
        "apply_url": contacts.get("apply_url"),
        "unknowns": unknowns,
        "status": "open",
    }


# Human job-function → FIND matcher tape_family (work physics, not a robot class).
JOB_FUNCTION_TAPE_FAMILY = {
    "picking": "pick_pack",
    "packing": "pick_pack",
    "material_handling": "warehouse",
    "receiving": "warehouse",
    "shipping": "logistics",
    "replenishment": "warehouse",
    "housekeeping": "hospitality",
    "environmental_services": "disinfection",
    "warewash": "food_prep",
    "food_prep": "food_prep",
    "serving": "serve",
    "cleaning": "scrub",
    "front_desk": "hospitality",
    "palletizing": "pallet",
    "patient_transport": "clinical_delivery",
    "pharmacy": "clinical_delivery",
    "laundry": "hospitality",
    "harvest": "agriculture",
    "field_work": "agriculture",
    "tractor": "agriculture",
    "weeding": "agriculture",
    "haulage": "mining",
    "drywall": "construction",
    "framing": "construction",
    "construction_labor": "construction",
    "machine_tending": "factory",
}

_BOARD_EMPLOYER_NAMES = frozenset(
    {
        "indeed",
        "simplyhired",
        "linkedin",
        "ziprecruiter",
        "glassdoor",
        "talent.com",
        "snagajob",
        "careerbuilder",
        "confidential",
        "not disclosed",
        "n/a",
        "na",
        "employer confidential",
    }
)


def tape_family_for_job_function(job_function: Optional[str]) -> Optional[str]:
    key = (job_function or "").strip().lower()
    if not key or key in {"work", "unknown", "unknown_function"}:
        return None
    return JOB_FUNCTION_TAPE_FAMILY.get(key)


_JOB_TITLE_AS_EMPLOYER_RE = re.compile(
    r"^(warehouse (?:associate|worker)|order picker|line cook|prep cook|"
    r"housekeeper|room attendant|farm worker|farm laborer|harvest worker|"
    r"construction laborer|machine operator|machine tender|cnc operator|"
    r"patient transporter|evs technician|server|dishwasher)$",
    re.I,
)


def is_job_employer_name(name: str, title: str = "") -> bool:
    """Real employer on a job posting — not a board, headline, or the job title itself."""
    n = (name or "").strip()
    if len(n) < 2 or len(n) > 80:
        return False
    low = n.lower().rstrip(".")
    if low in _BOARD_EMPLOYER_NAMES or "simplyhired" in low or low.startswith("indeed"):
        return False
    if title and low == (title or "").strip().lower():
        return False
    if _JOB_TITLE_AS_EMPLOYER_RE.match(low):
        return False
    try:
        from app.services.headline_name_shape import passes_headline_name_shape

        ok, _ = passes_headline_name_shape(n)
        if not ok:
            return False
    except Exception:
        pass
    return True


# Board inboxes that appear on aggregator pages. Not an employer mailbox.
_BOARD_EMAIL_DOMAINS = frozenset(
    {
        "indeed.com",
        "indeedmail.com",
        "ziprecruiter.com",
        "simplyhired.com",
        "glassdoor.com",
        "linkedin.com",
        "talent.com",
        "snagajob.com",
        "careerbuilder.com",
        "monster.com",
        "dice.com",
    }
)
_BOARD_EMAIL_EXACT = frozenset(
    {
        "noreply@indeed.com",
        "no-reply@indeed.com",
        "jobs@indeed.com",
        "noreply@ziprecruiter.com",
        "jobs@ziprecruiter.com",
        "noreply@simplyhired.com",
        "jobs@simplyhired.com",
        "noreply@glassdoor.com",
        "jobs@glassdoor.com",
        "noreply@linkedin.com",
        "jobs@linkedin.com",
    }
)
_BOARD_EMAIL_LOCALS = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "mailer-daemon",
        "postmaster",
        "bounce",
        "unsubscribe",
    }
)
_MAILTO_RE = re.compile(
    r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    re.I,
)
_ITEMPROP_EMAIL_RE = re.compile(
    r"""itemprop=["']email["'][^>]*>([^<]{3,320})""",
    re.I,
)
_ITEMPROP_EMAIL_CONTENT_RE = re.compile(
    r"""itemprop=["']email["'][^>]*content=["']([^"']+)["']""",
    re.I,
)


def _host_from_url(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""
    return host


def _is_board_host(host: str) -> bool:
    h = (host or "").lower().removeprefix("www.")
    if not h:
        return False
    return any(h == d or h.endswith("." + d) for d in _BOARD_EMAIL_DOMAINS)


def is_board_mailbox(email: str) -> bool:
    """True for aggregator/ATS notification inboxes, not a hiring employer."""
    hit = normalize_recipient_email(email)
    if not hit:
        return True
    if hit in _BOARD_EMAIL_EXACT:
        return True
    local, _, domain = hit.partition("@")
    if local in _BOARD_EMAIL_LOCALS:
        return True
    return _is_board_host(domain)


def _add_email(out: list[str], seen: set[str], raw: Any) -> None:
    if not isinstance(raw, str):
        return
    hit = normalize_recipient_email(raw)
    if not hit or hit in seen or is_board_mailbox(hit):
        return
    seen.add(hit)
    out.append(hit)


def _jsonld_as_dict(jsonld: Any) -> Optional[dict[str, Any]]:
    if isinstance(jsonld, str):
        try:
            jsonld = json.loads(jsonld)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(jsonld, list):
        for item in jsonld:
            parsed = _jsonld_as_dict(item)
            if parsed:
                return parsed
        return None
    if not isinstance(jsonld, dict):
        return None
    types = jsonld.get("@type")
    type_list = types if isinstance(types, list) else [types]
    if "JobPosting" in type_list or not types:
        return jsonld
    graph = jsonld.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            parsed = _jsonld_as_dict(item)
            if parsed:
                return parsed
    return jsonld


def _jsonld_emails(obj: dict[str, Any], out: list[str], seen: set[str]) -> None:
    _add_email(out, seen, obj.get("email"))
    for key in ("hiringOrganization", "applicationContact", "creator"):
        nested = obj.get(key)
        if isinstance(nested, list):
            nested = nested[0] if nested else None
        if isinstance(nested, dict):
            _add_email(out, seen, nested.get("email"))
            contact = nested.get("contactPoint") or nested.get("applicationContact")
            if isinstance(contact, list):
                contact = contact[0] if contact else None
            if isinstance(contact, dict):
                _add_email(out, seen, contact.get("email"))


def _jsonld_url(obj: dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        raw = obj.get(key)
        if isinstance(raw, dict):
            raw = raw.get("url") or raw.get("@id")
        if isinstance(raw, list) and raw:
            raw = raw[0]
        if isinstance(raw, str):
            text = raw.strip()
            if text.startswith("http://") or text.startswith("https://"):
                return text[:1024]
    return None


def _mailto_emails(blob: str, out: list[str], seen: set[str]) -> None:
    if not blob:
        return
    for match in _MAILTO_RE.finditer(blob):
        _add_email(out, seen, match.group(1))
    for match in _ITEMPROP_EMAIL_CONTENT_RE.finditer(blob):
        _add_email(out, seen, match.group(1))
    for match in _ITEMPROP_EMAIL_RE.finditer(blob):
        _add_email(out, seen, match.group(1).strip())


def extract_job_contacts(
    *,
    html: str = "",
    jsonld: Any = None,
    description: str = "",
    employer: str = "",
    title: str = "",
) -> dict[str, Optional[str]]:
    """Emails/URLs that appear on this posting. Never invent info@domain.

    Sources: mailto: hrefs, schema.org / JSON-LD ``email``,
    ``hiringOrganization.email``, ``applicationContact.email``.
    Skips Indeed/board mailboxes and title-as-company rows.
    """
    empty: dict[str, Optional[str]] = {
        "employer_email": None,
        "contact_url": None,
        "apply_url": None,
    }
    if employer and not is_job_employer_name(employer, title=title):
        return empty

    emails: list[str] = []
    seen: set[str] = set()
    posting = _jsonld_as_dict(jsonld) if jsonld is not None else None
    if posting:
        _jsonld_emails(posting, emails, seen)
        desc = posting.get("description")
        if isinstance(desc, str):
            _mailto_emails(desc, emails, seen)
    _mailto_emails(html or "", emails, seen)
    _mailto_emails(description or "", emails, seen)

    apply_url = None
    contact_url = None
    if posting:
        apply_url = _jsonld_url(posting, "url")
        org = posting.get("hiringOrganization") or {}
        if isinstance(org, list):
            org = org[0] if org else {}
        if isinstance(org, dict):
            org_url = _jsonld_url(org, "url", "sameAs")
            if org_url and not _is_board_host(_host_from_url(org_url)):
                contact_url = org_url
        app = posting.get("applicationContact")
        if isinstance(app, list):
            app = app[0] if app else None
        if isinstance(app, dict):
            app_url = _jsonld_url(app, "url")
            if app_url:
                apply_url = apply_url or app_url
                if not contact_url and not _is_board_host(_host_from_url(app_url)):
                    contact_url = app_url

    return {
        "employer_email": emails[0] if emails else None,
        "contact_url": contact_url,
        "apply_url": apply_url,
    }


def format_robot_job_signal(job: dict[str, Any]) -> str:
    title = job.get("job_title") or "Untitled work"
    function = job.get("job_function") or "unknown_function"
    pay = job.get("compensation") or {}
    wage = "pay unknown"
    if pay.get("wage_min") is not None:
        lo = pay["wage_min"]
        hi = pay.get("wage_max")
        unit = pay.get("wage_unit") or "hour"
        if hi and hi != lo:
            wage = f"${lo:g}–${hi:g}/{unit}"
        else:
            wage = f"${lo:g}/{unit}"
    specs = job.get("performance_specs") or {}
    bits = []
    if specs.get("throughput"):
        th = specs["throughput"]
        bits.append(f"{th['count']} {th['unit']}/{th['per']}")
    if specs.get("payload"):
        pl = specs["payload"]
        bits.append(f"{pl['value']} {pl['unit']}")
    if specs.get("shift"):
        bits.append(str(specs["shift"]))
    spec_s = ", ".join(bits) if bits else "specs unknown"
    status = job.get("status") or "open"
    employer = job.get("employer") or "unknown employer"
    return (
        f"ROBOT_JOB | {title} | {function} | {wage} | {spec_s} | {status} | {employer}"
    )

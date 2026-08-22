"""Extract Robot Job fields from a public job posting.

Unknown is valid. Do not invent wages, throughput, or FTE.
Used by job-board scrapers so SIGNAL labor_pain rows become employment objects.
"""
from __future__ import annotations

import re
from typing import Any, Optional

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
    ("room attendant", "housekeeping"),
    ("evs", "environmental_services"),
    ("environmental services", "environmental_services"),
    ("floor tech", "environmental_services"),
    ("dishwasher", "warewash"),
    ("line cook", "food_prep"),
    ("prep cook", "food_prep"),
    ("patient transport", "patient_transport"),
    ("pharmacy technician", "pharmacy"),
    ("laundry", "laundry"),
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


def job_function_from_title(title: str) -> Optional[str]:
    blob = (title or "").lower()
    if not blob:
        return None
    for needle, family in JOB_FUNCTION_BY_TITLE:
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
    return {
        "employer": (company or "").strip() or None,
        "workplace": (locality or "").strip() or None,
        "job_title": (title or "").strip() or None,
        "job_function": function,
        "compensation": pay,
        "performance_specs": specs,
        "source_url": source_url or None,
        "unknowns": unknowns,
        "status": "open",
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

"""FIND listing: robot company URL → named robots, then blurbs, then specs.

Jobs must not crawl every SKU page. Indexed OEMs skip live fetch and keep the
full named lineup. FIND *surfaces* three robots at a time (search pass / picker
page). That is not a cap on how many robots a company may have.

Unknown OEM homepages still parse names already on the page, in this order:

1. product names
2. a short description next to each name (if present)
3. payload / runtime numbers next to that name (if present)

Never invent a SKU or a spec.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

# How many robots FIND searches / shows per pass. Not a company roster cap.
FIND_PRODUCT_LIST_CAP = 3
# Homepage parse ceiling for unknown OEMs (no SKU-page crawl). Catalogs are uncapped.
FIND_LIVE_DISCOVERY_CAP = 24

_GENERIC_LINE = re.compile(
    r"^(agvs?|amrs?|agv\s*/\s*amr|mobile robots?|cobots?|industrial robots?|"
    r"systems?|fleet|robots?|robotics|platform|automation|agv systems?|"
    r"mobile robots|research(?:\s+(?:humanoid|platforms?|robots?))?)\.?$",
    re.I,
)
_GENERIC_TOKEN = re.compile(
    r"^(agv|amr|cobot|robot|robots|series|system|systems|fleet|platform|"
    r"solutions?|products?|line|research)$",
    re.I,
)
_SPLIT_LIST = re.compile(r"\s*(?:,|;|\||\band\b|&)\s*", re.I)
_PAYLOAD = re.compile(
    r"(?:payload|capacity|load)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(kg|lb|lbs)",
    re.I,
)
_RUNTIME = re.compile(
    r"(?:runtime|battery(?: life)?|operat\w+\s+time)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours?)",
    re.I,
)
_LEADING_COMPANY = re.compile(
    r"^(the\s+)?(inc|llc|ltd|gmbh|corp|co|ag|plc)\b",
    re.I,
)


def brand_token(company: str) -> str:
    raw = re.sub(r"\s+", " ", (company or "").strip())
    raw = re.sub(r"\s*[\(/].*$", "", raw).strip()
    parts = [p for p in re.split(r"\s+", raw) if p and not _LEADING_COMPANY.match(p)]
    if not parts:
        return ""
    first = re.sub(r"[^A-Za-z0-9+\-]", "", parts[0])
    if first.lower() in {"mobile", "boston", "universal", "clearpath"}:
        return " ".join(parts[:2]) if len(parts) > 1 else first
    return first


def split_primary_robots(raw: str, company: str = "") -> list[str]:
    """Turn a seed `primary_robots` string into named products (no company cap)."""
    text = re.sub(r"\s+", " ", (raw or "").strip())
    if not text or _GENERIC_LINE.fullmatch(text):
        return []
    names: list[str] = []
    for chunk in _SPLIT_LIST.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        names.extend(_expand_slash(chunk, company))
    out: list[str] = []
    seen: set[str] = set()
    for name in names:
        cleaned = _clean_product_name(name, company)
        if not cleaned:
            continue
        key = re.sub(r"[^a-z0-9]", "", cleaned.lower())
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def _expand_slash(chunk: str, company: str) -> list[str]:
    chunk = re.sub(r"\s+series$", "", chunk, flags=re.I).strip()
    if "/" not in chunk:
        return [chunk]
    parts = [re.sub(r"\s+series$", "", p, flags=re.I).strip() for p in chunk.split("/")]
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return parts
    if all(_GENERIC_LINE.fullmatch(p) or _GENERIC_TOKEN.fullmatch(p) for p in parts):
        return []
    first = parts[0]
    num = re.match(r"^(.*?)(\d+[A-Za-z]?)$", first.replace(" ", " "))
    rest_numeric = all(re.fullmatch(r"\d+[A-Za-z]?", p.replace(" ", "")) for p in parts[1:])
    if num and rest_numeric:
        prefix = num.group(1)
        expanded = [first]
        for part in parts[1:]:
            if prefix.endswith((" ", "-", "_")):
                expanded.append(f"{prefix}{part}")
            elif prefix and prefix[-1].isalpha():
                # MiR250/600 → MiR600 ; OTTO 100/750 → OTTO 750
                expanded.append(
                    f"{prefix}{part}" if " " not in first else f"{prefix}{part}"
                )
            else:
                expanded.append(f"{prefix}{part}".strip())
        return expanded
    if " " in first:
        brand = first.split()[0]
        out = [first]
        for part in parts[1:]:
            if part.lower().startswith(brand.lower()):
                out.append(part)
            else:
                out.append(f"{brand} {part}")
        return out
    return parts


def _clean_product_name(name: str, company: str) -> str | None:
    name = re.sub(r"\s+", " ", name).strip(" .-")
    name = re.sub(r"\s+\((?:series|family|line)\)$", "", name, flags=re.I)
    if not name or _GENERIC_LINE.fullmatch(name) or _GENERIC_TOKEN.fullmatch(name):
        return None
    if len(name) > 48:
        return None
    brand = brand_token(company)
    if (
        brand
        and " " not in name
        and len(name) <= 4
        and name.isupper()
        and brand.lower() not in name.lower()
    ):
        # LD / HD → Omron LD
        return f"{brand} {name}"
    return name


def format_listing_blurb(row: dict[str, Any] | None) -> str | None:
    """Description, then spec fragments. Never invent numbers."""
    row = row or {}
    desc = (row.get("description") or "").strip()
    specs = row.get("specs") if isinstance(row.get("specs"), dict) else {}
    extra: list[str] = []
    if specs.get("payload_kg") is not None:
        extra.append(f"Payload {specs['payload_kg']} kg")
    if specs.get("battery_life_h") is not None:
        extra.append(f"Runtime {specs['battery_life_h']} h")
    if extra:
        bits = ". ".join(extra) + "."
        desc = f"{desc} {bits}".strip() if desc else bits
    return desc or None


def listing_from_catalog(
    vendor: dict[str, Any] | None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Named robots already stored for a vendor. Names first; keep description/specs if present.

    `limit` is a FIND surface page, not a company cap. Omit it to return the lineup.
    """
    from app.services.oem_sku_discover import is_junk_sku_name, looks_like_named_sku

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for robot in (vendor or {}).get("robots") or []:
        name = str(robot.get("name") or "").strip()
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        if not name or key in seen:
            continue
        if is_junk_sku_name(name) and not looks_like_named_sku(name):
            continue
        seen.add(key)
        desc = (robot.get("description") or "").strip()
        if not desc:
            for claim in robot.get("catalog_claims") or []:
                span = str((claim or {}).get("evidence_span") or "").strip()
                if span:
                    desc = span
                    break
        specs = robot.get("specs") if isinstance(robot.get("specs"), dict) else {}
        slim = {k: v for k, v in specs.items() if v not in (None, "", 0, False)}
        rows.append(
            {
                "name": name,
                "description": desc or None,
                "display_class": (robot.get("primary_class") or "").strip() or None,
                "specs": slim or None,
            }
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def listing_from_page(
    names: list[str],
    text: str,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Attach nearby description then specs onto already-ranked product names."""
    from app.services.oem_sku_discover import is_junk_sku_name

    blob = text or ""
    rows: list[dict[str, Any]] = []
    kept = [n for n in names if n and not is_junk_sku_name(n)]
    chosen = kept if limit is None else kept[:limit]
    for name in chosen:
        window = _window_around(name, blob)
        rows.append(
            {
                "name": name,
                "description": _blurb_near(name, window),
                "display_class": None,
                "specs": _specs_near(window),
            }
        )
    return rows


def _window_around(name: str, text: str, radius: int = 420) -> str:
    if not name or not text:
        return text[:800]
    idx = text.lower().find(name.lower())
    if idx < 0:
        return text[:800]
    return text[max(0, idx) : idx + radius]


def _blurb_near(name: str, window: str) -> str | None:
    rest = window
    low = name.lower()
    if rest.lower().startswith(low):
        rest = rest[len(name) :].lstrip(" :-–—|,.")
    rest = re.sub(r"\s+", " ", rest).strip()
    if len(rest) < 24:
        return None
    match = re.match(r"(.{24,180}?)(?:[.!?\n]|$)", rest)
    if not match:
        return None
    blurb = match.group(1).strip()
    if len(blurb) < 24:
        return None
    return blurb[:180]


def _specs_near(window: str) -> dict[str, Any] | None:
    specs: dict[str, Any] = {}
    payload = _PAYLOAD.search(window or "")
    if payload:
        value = float(payload.group(1))
        unit = payload.group(2).lower()
        if unit.startswith("lb"):
            value = round(value * 0.453592, 2)
        specs["payload_kg"] = int(value) if value == int(value) else value
    runtime = _RUNTIME.search(window or "")
    if runtime:
        hours = float(runtime.group(1))
        specs["battery_life_h"] = int(hours) if hours == int(hours) else hours
    return specs or None


def host_from_website(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    host = (urlparse(raw).hostname or "").lower().removeprefix("www.")
    return host


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:80]


def listing_payload_for_url(url: str) -> dict[str, Any]:
    """Host-string OEM listing. No DNS, no live fetch, no Redis."""
    from app.services.vendor_robot_lookup import lookup_vendor_by_url

    vendor = lookup_vendor_by_url(url)
    if not vendor or not (vendor.get("robots") or []):
        return {
            "matched": False,
            "vendor_name": None,
            "vendor_url": None,
            "robots": [],
        }
    robots = listing_from_catalog(vendor)
    for row in robots:
        row["description"] = format_listing_blurb(row)
    if not robots:
        return {
            "matched": False,
            "vendor_name": None,
            "vendor_url": None,
            "robots": [],
        }
    return {
        "matched": True,
        "vendor_name": (vendor.get("vendor_name") or "").strip() or None,
        "vendor_url": (vendor.get("vendor_url") or "").strip() or None,
        "robots": robots,
    }

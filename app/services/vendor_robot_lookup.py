"""Vendor URL → robot SKUs from the /robots index (no homepage guessing).

Jobs resolve still crawls unknown OEMs. When the submitted host matches a
vendor we already indexed from readyforrobots.com/robots, return those SKUs
and a lightweight profile built from stored specs.

Industrial / commercial lists can append the same JSON shape later
(`list_category`).
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from app.services.robot_url_safety import registrable_domain

logger = logging.getLogger(__name__)

INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "vendor_robots_index.json"

# Press / CDN hosts that appear as product_url on thin catalog rows.
JUNK_LOOKUP_HOSTS = frozenset(
    {
        "aol.com",
        "msn.com",
        "tmcnet.com",
        "morningstar.com",
        "reuters.com",
        "forbes.com",
        "bloomberg.com",
        "yahoo.com",
        "finance.yahoo.com",
        "nasdaq.com",
        "therobotreport.com",
        "techcrunch.com",
        "wikipedia.org",
        "youtube.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "prnewswire.com",
        "businesswire.com",
        "humanoid.guide",
    }
)

VENDOR_HOME_FALLBACK = {
    "keenon robotics": "https://www.keenonrobot.com",
    "keenon": "https://www.keenonrobot.com",
    "ubtech / uworld": "https://www.ubtrobot.com",
    "ubtech robotics": "https://www.ubtrobot.com",
    "agibot (zhiyuan robotics)": "https://www.agibot.com",
    "agibot": "https://www.agibot.com",
    "unitree robotics": "https://www.unitree.com",
    "engineai": "https://www.engineai.com.cn",
    "faraday future": "https://www.ff.com",
    "realbotix": "https://www.realbotix.com",
    "primebot": "https://www.primebot.cn",
    "generative bionics": "https://gbionics.ai",
    "uma": "https://uma.bot",
    "shanghai electric": "https://www.shanghai-electric.com",
    "mentee robotics": "https://www.menteebot.com",
    "step robotics": "https://en.stepelectric.com",
    "dlr": "https://www.dlr.de",
}

SPEC_KEEP = (
    "payload_kg",
    "battery_life_h",
    "height_cm",
    "weight_kg",
    "top_speed_mps",
    "total_dof",
    "finger_count",
    "has_dexterous_hands",
    "autonomy_level",
    "can_climb_stairs",
    "has_sdk",
    "charge_time_h",
    "peak_torque_nm",
)

_SPEC_FACT = {
    "payload_kg": ("payload", "kg"),
    "battery_life_h": ("runtime", "h"),
    "height_cm": ("reach_or_workspace", "cm"),
    "weight_kg": ("weight", "kg"),
    "top_speed_mps": ("mobility", "m/s"),
    "total_dof": ("arm_count", None),
    "has_dexterous_hands": ("has_dexterous_hands", None),
    "autonomy_level": ("autonomy_or_control", None),
    "can_climb_stairs": ("mobility", None),
}


def host_from_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = (urlparse(raw).hostname or "").lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def lookup_domain(url: str | None) -> str:
    host = host_from_url(url)
    if not host:
        return ""
    return registrable_domain(host)


def is_junk_lookup_host(host: str) -> bool:
    h = (host or "").lower().removeprefix("www.")
    if not h:
        return True
    if h in JUNK_LOOKUP_HOSTS:
        return True
    root = registrable_domain(h)
    return root in JUNK_LOOKUP_HOSTS


def slim_specs(specs: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in SPEC_KEEP:
        val = (specs or {}).get(key)
        if val is None or val == "" or val == 0:
            continue
        out[key] = val
    return out


def profile_from_specs(
    *,
    robot_name: str,
    vendor_name: str,
    domain: str,
    product_url: str | None,
    specs: dict[str, Any] | None,
    list_category: str = "humanoid",
) -> dict[str, Any]:
    """Lightweight identity profile from the /robots index — not a live crawl."""
    slim = slim_specs(specs)
    facts: list[dict[str, Any]] = [
        {
            "predicate": "product_class",
            "value": list_category,
            "units": None,
            "epistemic": "explicit",
        }
    ]
    for spec_key, (predicate, units) in _SPEC_FACT.items():
        if spec_key not in slim:
            continue
        facts.append(
            {
                "predicate": predicate,
                "value": slim[spec_key],
                "units": units,
                "epistemic": "explicit",
            }
        )
    n = len(facts)
    if n >= 5:
        tier, coverage, level = "B", min(0.7, 0.15 * n), "medium"
    elif n >= 2:
        tier, coverage, level = "C", min(0.4, 0.12 * n), "low"
    else:
        tier, coverage, level = "C", 0.1, "low"
    source_url = product_url or f"https://{domain}" if domain else ""
    return {
        "profile_confidence": tier,
        "coverage_rate": coverage,
        "coverage_level": level,
        "source": "vendor_robots_index",
        "notes": [
            f"Indexed from readyforrobots.com/robots for {vendor_name}.",
            "Specs come from the public humanoid index, not a live OEM crawl.",
        ],
        "facts": facts,
        "sources": (
            [
                {
                    "url": source_url,
                    "source_type": "product",
                    "title": robot_name,
                    "publisher_role": "manufacturer",
                }
            ]
            if source_url
            else []
        ),
    }


@lru_cache(maxsize=1)
def load_vendor_robots_index(path: str | None = None) -> dict[str, Any]:
    target = Path(path) if path else INDEX_PATH
    if not target.exists():
        return {"vendors": [], "generated_at": None, "source": None}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("vendor_robots_index unreadable")
        return {"vendors": [], "generated_at": None, "source": None}
    if not isinstance(data, dict):
        return {"vendors": [], "generated_at": None, "source": None}
    data.setdefault("vendors", [])
    return data


def reload_vendor_robots_index() -> None:
    load_vendor_robots_index.cache_clear()


def _vendor_domain_map(index: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = index or load_vendor_robots_index()
    out: dict[str, dict[str, Any]] = {}
    for vendor in data.get("vendors") or []:
        for raw in vendor.get("domains") or []:
            domain = lookup_domain(str(raw)) or host_from_url(str(raw))
            if not domain or is_junk_lookup_host(domain):
                continue
            existing = out.get(domain)
            if existing is None:
                out[domain] = vendor
                continue
            if existing is vendor:
                continue
            robots = list(existing.get("robots") or [])
            seen = {r.get("model_slug") for r in robots}
            for robot in vendor.get("robots") or []:
                slug = robot.get("model_slug")
                if slug and slug not in seen:
                    robots.append(robot)
                    seen.add(slug)
            domains = list(existing.get("domains") or [])
            for host in vendor.get("domains") or []:
                if host not in domains:
                    domains.append(host)
            merged = dict(existing)
            merged["robots"] = robots
            merged["domains"] = domains
            out[domain] = merged
    return out


def lookup_vendor_by_url(url: str | None, *, index: dict[str, Any] | None = None) -> Optional[dict[str, Any]]:
    """Return the vendor record whose domain matches `url`, or None."""
    domain = lookup_domain(url)
    if not domain or is_junk_lookup_host(domain):
        return None
    table = _vendor_domain_map(index)
    hit = table.get(domain)
    if hit:
        return hit
    host = host_from_url(url)
    if host and host != domain:
        return table.get(host)
    return None


_GENERIC_PRODUCT_PATHS = frozenset(
    {
        "",
        "/",
        "/en",
        "/zh",
        "/cn",
        "/en-us",
        "/zh-cn",
        "/zh-hans",
        "/index",
        "/home",
        "/products",
        "/product",
    }
)
_LOCALE_ONLY_PATH = re.compile(r"^/(?:en|zh|ja|ko|de|fr|es|it|pt)(?:-[a-z]{2,4})?$", re.I)


def _is_sku_path(path: str) -> bool:
    p = (path or "").rstrip("/").lower() or "/"
    if p in _GENERIC_PRODUCT_PATHS:
        return False
    if _LOCALE_ONLY_PATH.match(p):
        return False
    return True


def select_index_robot(url: str | None, vendor: dict[str, Any]) -> Optional[dict[str, Any]]:
    """If the submitted URL is a product page, pick that SKU.

    Vendor homepages and locale roots (`/en`) must not select a SKU — the
    picker should show every indexed robot instead.
    """
    robots = vendor.get("robots") or []
    if not robots:
        return None
    submitted = (url or "").rstrip("/").lower()
    path = (urlparse(url or "").path or "").rstrip("/").lower()
    slug_from_path = path.rsplit("/", 1)[-1] if path else ""
    for robot in robots:
        product = (robot.get("product_url") or "").rstrip("/").lower()
        slug = (robot.get("model_slug") or "").lower()
        product_path = urlparse(product).path.rstrip("/") if product else ""
        if (
            product
            and _is_sku_path(product_path)
            and submitted.rstrip("/") == product
        ):
            return robot
        if not _is_sku_path(path):
            continue
        if slug and slug_from_path and slug_from_path in {slug, slug.split("-")[-1]}:
            return robot
        short = slug.split("-")[-1] if slug else ""
        if short and len(short) >= 2 and path and short == slug_from_path:
            return robot
    return None


def index_robot_names(vendor: dict[str, Any]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for robot in vendor.get("robots") or []:
        name = (robot.get("name") or "").strip()
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        if not name or key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names

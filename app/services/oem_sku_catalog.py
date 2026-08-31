"""OEM/SKU catalog from the operator spreadsheet — identity only.

COMPANY → PRODUCT (named SKU) → CONFIGURATION (default stub).
Does not invent capabilities, payloads, or prices. Empty specs stay UNKNOWN.
Wrong product URLs (Stretch on the Spot page) are flagged and never stored.
"""
from __future__ import annotations

import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

from app.services.vendor_robot_lookup import (
    JUNK_LOOKUP_HOSTS,
    host_from_url,
    lookup_domain,
)

ROOT = Path(__file__).resolve().parents[2]
XLSX_PATH = ROOT / "docs" / "reference" / "readyforrobots_companies_and_robots.xlsx"
ONTOLOGY_PATH = ROOT / "ontology" / "oem_sku_catalog.v1.json"
VERTICAL_CATALOG_PATH = ROOT / "ontology" / "vertical_oem_sku_catalog.v1.json"
MIXED_OEM_CATALOG_PATH = ROOT / "ontology" / "mixed_oem_sku_catalog.v1.json"
SEED_PATH = ROOT / "app" / "data" / "vendor_robots_oem_sku_seed.json"
LOOKUP_PATH = ROOT / "app" / "data" / "oem_sku_url_lookup.json"
DISCOVERY_PATH = ROOT / "app" / "data" / "oem_sku_discovery.json"

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_SPLIT_URLS = re.compile(r"[\n\r|;]+")
_GENERIC_NAME = re.compile(
    r"(inventory robot|shelf scanner|meal assembly|delivery robot|"
    r"storage robot|palletizing robot|robotic kitchen|series)$",
    re.I,
)
_FAMILY_BLOB = re.compile(
    r"\b(ur series|e-series|crx series|amr scrubbers)\b",
    re.I,
)

# Known bad spreadsheet URLs: Stretch was pasted onto the Spot page.
_WRONG_PRODUCT_PATH = (
    (("stretch",), ("spot",)),
)


def slugify(value: str) -> str:
    text = (
        (value or "")
        .lower()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("'", "")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return slug[:80] or "sku"


def name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def map_primary_class(category: str, klass: str) -> str:
    blob = f"{category} {klass}".lower()
    if "humanoid" in blob or "bipedal" in blob:
        return "humanoid"
    if "serving" in blob or "waiter" in blob or "table service" in blob:
        return "serving"
    if "collaborative" in blob or "cobot" in blob:
        return "cobot"
    if "industrial robot" in blob:
        return "industrial_arm"
    if "amr" in blob or "warehouse" in blob:
        return "amr"
    if "drone" in blob and any(
        w in blob for w in ("clean", "wash", "facade", "window", "exterior")
    ):
        return "cleaning_drone"
    if "cleaning" in blob or "scrubber" in blob:
        return "cleaning_robot"
    if "inspection" in blob or "quadruped" in blob:
        return "quadruped"
    if "delivery" in blob:
        return "delivery_robot"
    if "surgical" in blob:
        return "surgical_robot"
    if "aerospace" in blob or "satellite" in blob or "orbital" in blob:
        return "aerospace_robot"
    if "avionics" in blob or "drone" in blob or "evtol" in blob or "eVTOL" in blob:
        return "aviation_robot"
    if "agriculture" in blob or "tractor" in blob or "combine" in blob or "weeder" in blob:
        return "agricultural_robot"
    if "construction" in blob or "jobsite" in blob:
        return "construction_robot"
    if "marine" in blob:
        return "marine_robot"
    return "service_robot"


def _col_row(ref: str) -> tuple[int, int]:
    col = "".join(c for c in ref if c.isalpha())
    row = int("".join(c for c in ref if c.isdigit()))
    n = 0
    for c in col:
        n = n * 26 + (ord(c.upper()) - 64)
    return n, row


def _read_xlsx_sheet(xlsx: Path, sheet_path: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(xlsx) as zf:
        xml = ET.fromstring(zf.read(sheet_path))
    cells: dict[int, dict[int, str]] = {}
    for node in xml.findall(".//m:c", _NS):
        ref = node.attrib.get("r")
        if not ref:
            continue
        col, row = _col_row(ref)
        inline = node.find("m:is", _NS)
        value_el = node.find("m:v", _NS)
        val = ""
        if node.attrib.get("t") == "inlineStr" and inline is not None:
            val = "".join(t.text or "" for t in inline.findall(".//m:t", _NS))
        elif value_el is not None:
            val = value_el.text or ""
        cells.setdefault(row, {})[col] = val
    if not cells:
        return []
    header_row = min(cells)
    max_col = max(max(row) for row in cells.values())
    headers = [cells.get(header_row, {}).get(i, f"col_{i}").strip() or f"col_{i}" for i in range(1, max_col + 1)]
    out: list[dict[str, str]] = []
    for r in range(header_row + 1, max(cells) + 1):
        row = {headers[i]: (cells.get(r, {}).get(i + 1) or "").strip() for i in range(len(headers))}
        if any(row.values()):
            out.append(row)
    return out


def _split_urls(raw: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for part in _SPLIT_URLS.split(raw or ""):
        url = part.strip()
        if not url:
            continue
        if "://" not in url:
            url = "https://" + url
        if url not in seen:
            out.append(url)
            seen.add(url)
    return out


def is_wrong_product_url(sku_name: str, url: str, *, sibling_names: list[str] | None = None) -> bool:
    """True when the URL is clearly another product (Stretch → Spot)."""
    path = (urlparse(url).path or "").lower()
    host = host_from_url(url)
    if not path and not host:
        return False
    sku = name_key(sku_name)
    for self_tokens, other_tokens in _WRONG_PRODUCT_PATH:
        if any(name_key(t) in sku for t in self_tokens) and any(t in path for t in other_tokens):
            if not any(t in path for t in self_tokens):
                return True
    siblings = sibling_names or []
    sku_token = _path_token(sku_name)
    if not sku_token:
        return False
    if sku_token in path:
        return False
    for sib in siblings:
        token = _path_token(sib)
        if token and token != sku_token and token in path:
            return True
    return False


def _path_token(name: str) -> str:
    key = name_key(name)
    if len(key) < 4:
        return ""
    return key


def parse_workbook(path: Path | None = None) -> dict[str, Any]:
    xlsx = path or XLSX_PATH
    if not xlsx.is_file():
        raise FileNotFoundError(f"OEM/SKU workbook missing: {xlsx}")
    companies_raw = _read_xlsx_sheet(xlsx, "xl/worksheets/sheet1.xml")
    robots_raw = _read_xlsx_sheet(xlsx, "xl/worksheets/sheet2.xml")

    companies: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for row in companies_raw:
        name = (row.get("Company") or "").strip()
        if not name:
            continue
        sources = _split_urls(row.get("Source URLs") or "")
        hosts: list[str] = []
        for url in sources:
            domain = lookup_domain(url) or host_from_url(url)
            if domain and domain not in JUNK_LOOKUP_HOSTS and domain not in hosts:
                hosts.append(domain)
        rec = {
            "name": name,
            "slug": slugify(name),
            "vendor_role": "robot_oem",
            "regions": (row.get("Regions") or "").strip() or None,
            "categories": [p.strip() for p in (row.get("Categories") or "").split(",") if p.strip()],
            "source_urls": sources,
            "domains": hosts,
            "price_indication": (row.get("Price indication") or "").strip() or None,
            "products": [],
        }
        companies.append(rec)
        by_name[name_key(name)] = rec

    skipped: list[dict[str, str]] = []
    products: list[dict[str, Any]] = []
    for row in robots_raw:
        sku = (row.get("Name") or "").strip()
        maker = (row.get("Maker") or "").strip()
        if not sku or not maker:
            skipped.append({"name": sku or "?", "reason": "missing_name_or_maker"})
            continue
        if _FAMILY_BLOB.search(sku):
            skipped.append({"name": sku, "maker": maker, "reason": "family_blob"})
            continue
        company = by_name.get(name_key(maker))
        if company is None:
            company = {
                "name": maker,
                "slug": slugify(maker),
                "vendor_role": "robot_oem",
                "regions": (row.get("Region") or "").strip() or None,
                "categories": [p.strip() for p in (row.get("Category") or "").split(",") if p.strip()],
                "source_urls": [],
                "domains": [],
                "products": [],
            }
            companies.append(company)
            by_name[name_key(maker)] = company
        source = (row.get("Source") or "").strip()
        source_urls = _split_urls(source)
        siblings = [r.get("Name") or "" for r in robots_raw if (r.get("Maker") or "").strip() == maker]
        flags: list[str] = []
        if _GENERIC_NAME.search(sku):
            flags.append("descriptive_name")
        usable_sources: list[str] = []
        for url in source_urls:
            if is_wrong_product_url(sku, url, sibling_names=siblings):
                flags.append("wrong_product_url")
                continue
            usable_sources.append(url)
        primary = map_primary_class(row.get("Category") or "", row.get("Class") or "")
        product = {
            "name": sku,
            "slug": f"{company['slug']}-{slugify(sku)}"[:160],
            "company_name": company["name"],
            "company_slug": company["slug"],
            "primary_class": primary,
            "category": (row.get("Category") or "").strip() or None,
            "listed_class": (row.get("Class") or "").strip() or None,
            "task": (row.get("Task") or "").strip() or None,
            "setting": (row.get("Setting") or "").strip() or None,
            "status": (row.get("Status") or "").strip() or None,
            "region": (row.get("Region") or "").strip() or None,
            "spreadsheet_sources": source_urls,
            "candidate_sources": usable_sources,
            "product_url": None,
            "lookup_host": None,
            "url_status": "unverified",
            "specs": {},
            "capability_confidence": "UNKNOWN",
            "flags": flags,
            "source": "workbook",
        }
        company["products"].append(product)
        products.append(product)

    return {
        "ontology_id": "oem_sku_catalog_v1",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "docs/reference/readyforrobots_companies_and_robots.xlsx",
        "rule": "COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES",
        "notes": [
            "Named SKUs only. Family blobs skipped.",
            "Empty specs stay UNKNOWN — do not invent payload, reach, or price.",
            "Quote required is not a spec.",
            "product_url / lookup_host are set only after a live fetch verifies the page.",
            "Stretch-on-Spot and other sibling-SKU URLs are flagged, never stored.",
        ],
        "company_count": len(companies),
        "product_count": len(products),
        "skipped": skipped,
        "companies": companies,
    }


def apply_verified_urls(catalog: dict[str, Any], lookup: dict[str, Any]) -> dict[str, Any]:
    """Copy fetched/verified URLs onto catalog products. Never copy unverified rows."""
    by_slug = {
        row["slug"]: row
        for row in (lookup.get("verified") or [])
        if row.get("slug") and row.get("url")
    }
    for company in catalog.get("companies") or []:
        for product in company.get("products") or []:
            hit = by_slug.get(product.get("slug"))
            if not hit:
                continue
            url = (hit.get("url") or "").strip()
            host = lookup_domain(url) or host_from_url(url)
            if not url or not host or host in JUNK_LOOKUP_HOSTS:
                continue
            if is_wrong_product_url(product["name"], url, sibling_names=[p["name"] for p in company["products"]]):
                continue
            product["product_url"] = url
            product["lookup_host"] = host
            product["url_status"] = "verified"
            if host not in (company.get("domains") or []):
                company.setdefault("domains", []).append(host)
            if url and url not in (company.get("verified_urls") or []):
                company.setdefault("verified_urls", []).append(url)
    return catalog


def merge_mixed_oem_catalog(
    catalog: dict[str, Any],
    mixed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge mixed-morphology OEM SKUs (humanoid + serving + cleaning + quadruped)."""
    if mixed is None:
        if not MIXED_OEM_CATALOG_PATH.is_file():
            return catalog
        try:
            mixed = json.loads(MIXED_OEM_CATALOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return catalog
    return merge_vertical_catalog(catalog, mixed)


def merge_extra_sku_catalogs(catalog: dict[str, Any]) -> dict[str, Any]:
    """Vertical + mixed-morphology overlays. Workbook parse must not wipe them."""
    return merge_mixed_oem_catalog(merge_vertical_catalog(catalog))


def merge_vertical_catalog(
    catalog: dict[str, Any],
    vertical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge verified vertical OEMs after workbook parse so they are not wiped."""
    if vertical is None:
        if not VERTICAL_CATALOG_PATH.is_file():
            return catalog
        try:
            vertical = json.loads(VERTICAL_CATALOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return catalog
    by_slug = {c.get("slug"): c for c in catalog.get("companies") or [] if c.get("slug")}
    for company in vertical.get("companies") or []:
        slug = company.get("slug")
        if not slug:
            continue
        if slug not in by_slug:
            catalog.setdefault("companies", []).append(company)
            by_slug[slug] = company
            continue
        existing = by_slug[slug]
        have = {p.get("slug"): p for p in existing.get("products") or [] if p.get("slug")}
        for product in company.get("products") or []:
            pslug = product.get("slug")
            if not pslug:
                continue
            if pslug not in have:
                existing.setdefault("products", []).append(product)
                have[pslug] = product
                continue
            row = have[pslug]
            for key in (
                "listed_class",
                "task",
                "setting",
                "product_url",
                "lookup_host",
                "url_status",
                "primary_class",
                "configuration_kind",
                "host_platform",
                "region",
            ):
                val = product.get(key)
                if val in (None, ""):
                    continue
                if key in {"configuration_kind", "host_platform"} and val in {"standalone", "none"}:
                    continue
                row[key] = val
            if product.get("product_url") and not row.get("product_url"):
                row["product_url"] = product["product_url"]
        for domain in company.get("domains") or []:
            if domain and domain not in (existing.get("domains") or []):
                existing.setdefault("domains", []).append(domain)
        for url in company.get("source_urls") or []:
            if url and url not in (existing.get("source_urls") or []):
                existing.setdefault("source_urls", []).append(url)
    catalog["company_count"] = len(catalog.get("companies") or [])
    catalog["product_count"] = sum(len(c.get("products") or []) for c in catalog.get("companies") or [])
    return catalog


def _seed_catalog_claims(product: dict[str, Any]) -> list[dict[str, Any]]:
    """Identity claims only. Empty specs stay UNKNOWN."""
    cls = (product.get("primary_class") or "").strip()
    name = product.get("name") or "SKU"
    desc = _description(product)
    claims: list[dict[str, Any]] = []
    if cls:
        claims.append(
            {
                "predicate": "product_class",
                "value": cls,
                "evidence_span": desc or f"{name} indexed class {cls}.",
            }
        )
    class_claim = {
        "agricultural_robot": ("claims_agriculture", True),
        "agriculture": ("claims_agriculture", True),
        "construction_robot": ("claims_construction", True),
        "construction": ("claims_construction", True),
        "aviation_robot": ("claims_avionics", True),
        "avionics": ("claims_avionics", True),
        "drone": ("claims_avionics", True),
        "evtol": ("claims_avionics", True),
        "aerospace_robot": ("claims_aerospace", True),
        "aerospace": ("claims_aerospace", True),
        "marine_robot": ("claims_marine", True),
        "marine": ("claims_marine", True),
    }.get(cls)
    if class_claim:
        pred, val = class_claim
        claims.append({"predicate": pred, "value": val, "evidence_span": desc or f"{name}: {pred}."})
    kind = product.get("configuration_kind")
    host = product.get("host_platform")
    if kind:
        claims.append(
            {
                "predicate": "configuration_kind",
                "value": kind,
                "evidence_span": f"{name} configuration {kind}.",
            }
        )
    if host:
        claims.append(
            {
                "predicate": "host_platform",
                "value": host,
                "evidence_span": f"{name} host platform {host}.",
            }
        )
    claims.extend(_work_kind_claims(product, name, desc))
    return claims


def _work_kind_claims(product: dict[str, Any], name: str, desc: str) -> list[dict[str, Any]]:
    """SKU work-kind facts from listed_class/task — not company category."""
    blob = " ".join(
        str(product.get(k) or "")
        for k in ("name", "listed_class", "task", "setting", "primary_class")
    ).lower()
    blob = f"{blob} {desc.lower()}".strip()
    out: list[dict[str, Any]] = []

    def add(pred: str, value: Any, span: str) -> None:
        out.append({"predicate": pred, "value": value, "evidence_span": span})

    if re.search(r"weed|laserweed|laser weeder", blob):
        add("claims_weeding", True, f"{name}: weeding work on this configuration.")
    if re.search(r"\b(combine|lexion|grain harvest|header)\b", blob):
        add("claims_combine_harvest", True, f"{name}: combine grain harvest.")
    if re.search(r"\b(spray|see\s*&\s*spray|see and spray|ara)\b", blob) and "micro-spray" not in blob:
        add("claims_precision_spray", True, f"{name}: precision spray.")
    if re.search(r"\b(autonomous tractor|tractor for planting|mk-?v)\b", blob) and "implement" not in blob:
        add("claims_tractor_work", True, f"{name}: autonomous tractor field work.")
    if re.search(r"\b(3d print|3d-print|vulcan|bod2)\b", blob):
        add("claims_construction_print", True, f"{name}: 3D-print construction.")
    if re.search(r"\b(block-lay|block laying|brick|hadrian)\b", blob):
        add("claims_construction_block", True, f"{name}: block/brick laying.")
    if re.search(r"\b(fieldprinter|layout printer|floor layout|siteprint)\b", blob):
        add("claims_construction_layout", True, f"{name}: jobsite layout print.")
    if re.search(r"\bautonomous\b", blob) and re.search(r"\b(evtol|e-vtol)\b", blob):
        add("autonomy_mode", "autonomous", f"{name}: autonomous eVTOL configuration fact.")
    return out


def compile_vendor_seed(catalog: dict[str, Any]) -> dict[str, Any]:
    """FIND index shape. Hosts come from the spreadsheet; product_url only if verified."""
    vendors: list[dict[str, Any]] = []
    for company in catalog.get("companies") or []:
        domains = [d for d in (company.get("domains") or []) if d and d not in JUNK_LOOKUP_HOSTS]
        if not domains:
            continue
        robots: list[dict[str, Any]] = []
        vendor_url = f"https://{domains[0]}"
        for product in company.get("products") or []:
            if "wrong_product_url" in (product.get("flags") or []) and not product.get("product_url"):
                # Keep the named SKU for company identity; omit the bad URL.
                pass
            product_url = product.get("product_url") or ""
            robots.append(
                {
                    "name": product["name"],
                    "model_slug": product["slug"],
                    "product_url": product_url or None,
                    "vendor_url": vendor_url,
                    "primary_class": product.get("primary_class") or "service_robot",
                    "status": "available",
                    "country": product.get("region"),
                    "description": _description(product),
                    "lookup_host": product.get("lookup_host") or domains[0],
                    "url_status": product.get("url_status") or "unverified",
                    "capability_confidence": "UNKNOWN",
                    "catalog_claims": _seed_catalog_claims(product),
                    "specs": {},
                    "configuration_kind": product.get("configuration_kind") or "standalone",
                    "host_platform": product.get("host_platform") or "none",
                }
            )
        if not robots:
            continue
        vendors.append(
            {
                "vendor_name": company["name"],
                "domains": domains,
                "vendor_url": vendor_url,
                "list_category": "oem_sku",
                "robots": robots,
            }
        )
    return {
        "generated_at": catalog.get("generated_at"),
        "source": catalog.get("source"),
        "list_category": "oem_sku",
        "notes": catalog.get("notes") or [],
        "vendor_count": len(vendors),
        "robot_count": sum(len(v["robots"]) for v in vendors),
        "vendors": vendors,
    }


def _description(product: dict[str, Any]) -> str:
    bits = [b for b in (product.get("task"), product.get("setting")) if b]
    if not bits:
        return ""
    return f"{product['name']}: " + ". ".join(bits) + "."


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sku_terms(name: str) -> list[str]:
    raw = re.sub(r"[/_,]+", " ", name or "")
    parts = [p for p in re.split(r"\s+", raw) if len(p) >= 2]
    if name and name not in parts:
        parts.insert(0, name)
    return parts


def page_mentions_sku(text: str, sku: str, company: str = "") -> bool:
    blob = text or ""
    if not blob:
        return False
    if len(name_key(sku)) >= 4 and re.search(rf"\b{re.escape(sku)}\b", blob, re.I):
        return True
    if len(name_key(sku)) < 4 and company and company.lower() in blob.lower():
        return bool(re.search(rf"\b{re.escape(sku)}\b", blob, re.I))
    return False


def choose_product_link(
    links: list[tuple[str, str]],
    *,
    sku: str,
    company_host: str,
    sibling_names: list[str],
) -> Optional[str]:
    sku_token = _path_token(sku)
    if not sku_token:
        return None
    scored: list[tuple[int, str]] = []
    for href, anchor in links:
        if not href:
            continue
        host = host_from_url(href)
        if company_host and host and lookup_domain(host) != lookup_domain(company_host) and host != company_host:
            continue
        if is_wrong_product_url(sku, href, sibling_names=sibling_names):
            continue
        path = (urlparse(href).path or "").lower()
        label = f"{anchor} {path}"
        if sku_token not in name_key(label) and sku_token not in name_key(path):
            continue
        score = 2 if sku_token in name_key(path) else 1
        scored.append((score, href))
    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else None


def lookup_urls(
    catalog: dict[str, Any],
    *,
    fetch_page: Callable[..., Any] | None = None,
    rate_limit_s: float = 0.5,
    max_fetches: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch candidate pages with the Understanding fetcher. Store only verified URLs."""
    if fetch_page is None:
        from app.services.robot_understanding_v1.fetch import fetch_page as _fetch

        fetch_page = _fetch

    verified: list[dict[str, Any]] = list((prior or {}).get("verified") or [])
    skipped: list[dict[str, Any]] = list((prior or {}).get("skipped") or [])
    failed: list[dict[str, Any]] = list((prior or {}).get("failed") or [])
    queued: list[dict[str, Any]] = []
    done = {
        row.get("slug")
        for bucket in (verified, skipped, failed)
        for row in bucket
        if row.get("slug")
    }
    cache: dict[str, Any] = {}
    fetches = 0

    def _get(url: str):
        nonlocal fetches
        if url in cache:
            return cache[url]
        if max_fetches is not None and fetches >= max_fetches:
            return None
        if fetches:
            sleep(rate_limit_s)
        fetches += 1
        try:
            page = fetch_page(url, allow_archive=False)
        except Exception as exc:
            cache[url] = exc
            return exc
        cache[url] = page
        return page

    for company in catalog.get("companies") or []:
        siblings = [p["name"] for p in company.get("products") or []]
        company_host = (company.get("domains") or [""])[0]
        for product in company.get("products") or []:
            if product.get("slug") in done:
                continue
            candidates = list(product.get("candidate_sources") or [])
            if not candidates:
                skipped.append(
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "reason": "wrong_product_url" if "wrong_product_url" in product.get("flags", []) else "no_candidate",
                    }
                )
                continue
            if max_fetches is not None and fetches >= max_fetches:
                queued.append({"slug": product["slug"], "name": product["name"], "candidates": candidates})
                continue
            page = _get(candidates[0])
            if page is None:
                queued.append({"slug": product["slug"], "name": product["name"], "candidates": candidates})
                continue
            if isinstance(page, Exception) or getattr(page, "status_code", 0) != 200:
                failed.append(
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "url": candidates[0],
                        "reason": type(page).__name__ if isinstance(page, Exception) else f"http_{getattr(page, 'status_code', 0)}",
                    }
                )
                continue
            text = f"{getattr(page, 'title', '') or ''} {getattr(page, 'text', '') or ''}"
            links = list(getattr(page, "links", None) or [])
            product_href = choose_product_link(
                [(urljoin(candidates[0], href), anchor) for href, anchor in links],
                sku=product["name"],
                company_host=company_host,
                sibling_names=siblings,
            )
            chosen = candidates[0]
            chosen_page = page
            if product_href and product_href.rstrip("/") != candidates[0].rstrip("/"):
                follow = _get(product_href)
                if follow is not None and not isinstance(follow, Exception) and getattr(follow, "status_code", 0) == 200:
                    follow_text = f"{getattr(follow, 'title', '') or ''} {getattr(follow, 'text', '') or ''}"
                    if page_mentions_sku(follow_text, product["name"], company["name"]):
                        if not is_wrong_product_url(product["name"], getattr(follow, "final_url", product_href) or product_href, sibling_names=siblings):
                            chosen = getattr(follow, "final_url", None) or product_href
                            chosen_page = follow
                            text = follow_text
            if is_wrong_product_url(product["name"], chosen, sibling_names=siblings):
                skipped.append({"slug": product["slug"], "name": product["name"], "url": chosen, "reason": "wrong_product_url"})
                continue
            mentions = page_mentions_sku(text, product["name"], company["name"])
            if not mentions and not page_mentions_sku(text, company["name"]):
                failed.append(
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "url": chosen,
                        "reason": "sku_not_on_page",
                    }
                )
                continue
            # Company homepage that names the SKU, or a product page we followed.
            url_to_store = chosen if mentions else None
            if url_to_store:
                host = lookup_domain(url_to_store) or host_from_url(url_to_store)
                verified.append(
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "company": company["name"],
                        "url": url_to_store,
                        "host": host,
                        "status_code": getattr(chosen_page, "status_code", 200),
                    }
                )
            else:
                skipped.append(
                    {
                        "slug": product["slug"],
                        "name": product["name"],
                        "url": chosen,
                        "reason": "company_page_only",
                    }
                )

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fetcher": "app.services.robot_understanding_v1.fetch.fetch_page",
        "fetches": fetches,
        "verified": verified,
        "skipped": skipped,
        "failed": failed,
        "queued": queued,
        "counts": {
            "verified": len(verified),
            "skipped": len(skipped),
            "failed": len(failed),
            "queued": len(queued),
            "fetches": fetches,
        },
    }


def apply_to_catalog(seed: dict[str, Any], db=None) -> dict[str, int]:
    """Upsert manufacturers + robot_models. FIND tables — not a parallel robots table."""
    from sqlalchemy.orm import Session

    from app.models.robot_catalog import Manufacturer, RobotFamily, RobotModel

    close = False
    if db is None:
        from app.database import SessionLocal

        db = SessionLocal()
        close = True
    assert isinstance(db, Session)
    stats = {"manufacturers": 0, "models": 0, "updated": 0}
    try:
        for vendor in seed.get("vendors") or []:
            domain = (vendor.get("domains") or [None])[0]
            website = vendor.get("vendor_url") or (f"https://{domain}" if domain else None)
            slug = slugify(vendor.get("vendor_name") or domain or "vendor")
            mfr = db.query(Manufacturer).filter(Manufacturer.slug == slug).one_or_none()
            if mfr is None and domain:
                mfr = (
                    db.query(Manufacturer)
                    .filter(Manufacturer.lookup_host == domain)
                    .one_or_none()
                    if hasattr(Manufacturer, "lookup_host")
                    else None
                )
            if mfr is None:
                mfr = Manufacturer(
                    slug=slug,
                    name=vendor["vendor_name"],
                    website=website,
                    vendor_role="robot_oem",
                    vendor_type="oem",
                    verification_status="indexed",
                    source_url=seed.get("source"),
                    notes="OEM/SKU catalog from operator workbook. Specs UNKNOWN.",
                    external_refs={"oem_sku_catalog": True, "domains": vendor.get("domains")},
                )
                if hasattr(mfr, "lookup_host"):
                    mfr.lookup_host = domain
                db.add(mfr)
                db.flush()
                stats["manufacturers"] += 1
            else:
                if website and not mfr.website:
                    mfr.website = website
                if hasattr(mfr, "lookup_host") and domain and not mfr.lookup_host:
                    mfr.lookup_host = domain
                refs = dict(mfr.external_refs or {})
                refs["oem_sku_catalog"] = True
                mfr.external_refs = refs
                stats["updated"] += 1

            family_slug = "catalog"
            family = (
                db.query(RobotFamily)
                .filter(RobotFamily.manufacturer_id == mfr.id, RobotFamily.slug == family_slug)
                .one_or_none()
            )
            if family is None:
                family = RobotFamily(
                    manufacturer_id=mfr.id,
                    slug=family_slug,
                    name="Catalog",
                    primary_class=None,
                )
                db.add(family)
                db.flush()

            for robot in vendor.get("robots") or []:
                model_slug = (robot.get("model_slug") or slugify(robot["name"]))[:160]
                model = db.query(RobotModel).filter(RobotModel.slug == model_slug).one_or_none()
                product_url = robot.get("product_url") or None
                host = robot.get("lookup_host") or (lookup_domain(product_url) if product_url else domain)
                payload = {
                    "name": robot["name"],
                    "primary_class": robot.get("primary_class") or "service_robot",
                    "product_url": product_url,
                    "commercial_maturity": "unknown",
                    "capability_stubs": [],
                    "external_refs": {
                        "oem_sku_catalog": True,
                        "url_status": robot.get("url_status"),
                        "capability_confidence": "UNKNOWN",
                        "lookup_host": host,
                    },
                    "is_active": True,
                }
                if model is None:
                    model = RobotModel(
                        manufacturer_id=mfr.id,
                        family_id=family.id,
                        slug=model_slug,
                        **payload,
                    )
                    if hasattr(model, "lookup_host"):
                        model.lookup_host = host
                    db.add(model)
                    stats["models"] += 1
                else:
                    for key, val in payload.items():
                        if key == "product_url" and not val:
                            continue
                        setattr(model, key, val)
                    if hasattr(model, "lookup_host") and host and not model.lookup_host:
                        model.lookup_host = host
                    stats["updated"] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if close:
            db.close()
    return stats

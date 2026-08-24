#!/usr/bin/env python3
"""Compile robot_vendor_seed_v1.json → vendor_robots_jobs_seed.json.

Additional OEM companies for FIND: website → named robots (names, then
description, then specs if the seed has them). Does not crawl product pages.
FIND still searches three robots at a time. Skips vendors already in the
humanoid/commercial index so richer SKUs win.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.jobs_oem_listing import (  # noqa: E402
    host_from_website,
    slugify,
    split_primary_robots,
)
from app.services.vendor_robot_lookup import (  # noqa: E402
    JUNK_LOOKUP_HOSTS,
    lookup_domain,
)

SEED = ROOT / "docs" / "calibration" / "robot_vendor_seed_v1.json"
HUMANOID = ROOT / "app" / "data" / "vendor_robots_index.json"
COMMERCIAL = ROOT / "app" / "data" / "vendor_robots_commercial_seed.json"
INDUSTRIAL = ROOT / "app" / "data" / "vendor_robots_industrial_seed.json"
OUT = ROOT / "app" / "data" / "vendor_robots_jobs_seed.json"

CATEGORY_CLASS = {
    "amr_agv_material_transport": "amr",
    "autonomous_forklift_pallet": "amr",
    "industrial_robot_arms": "industrial_arm",
    "cobots": "cobot",
    "picking_manipulation_palletizing": "mobile_manipulator",
    "humanoids_general_purpose": "humanoid",
    "cleaning_robots": "cleaning_robot",
    "hospitality_foodservice_delivery": "service_robot",
    "inspection_security_quadrupeds": "quadruped",
    "agriculture": "agricultural_robot",
    "construction": "construction_robot",
    "healthcare_hospital_service": "service_robot",
    "last_mile_outdoor_delivery": "delivery_robot",
    "specialty_commercial": "service_robot",
}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _existing_domains() -> set[str]:
    out: set[str] = set()
    for path in (HUMANOID, COMMERCIAL, INDUSTRIAL):
        for vendor in (_load_json(path).get("vendors") or []):
            for raw in vendor.get("domains") or []:
                domain = lookup_domain(str(raw)) or host_from_website(str(raw))
                if domain:
                    out.add(domain)
            url_domain = lookup_domain(vendor.get("vendor_url"))
            if url_domain:
                out.add(url_domain)
    return out


def _alias_domains(company: str, host: str, domain: str) -> list[str]:
    """Extra FIND hosts for the same OEM listing — never a consumer mega-site."""
    aliases: list[str] = []
    low = (company or "").lower()
    if host in {"global.abb"} or "(abb)" in low or low.startswith("abb "):
        aliases.extend(["abb.com", "new.abb.com"])
    if "yaskawa" in low or host in {"motoman.com"}:
        aliases.extend(["yaskawa.com", "yaskawa-global.com", "motoman.com"])
    out: list[str] = []
    seen = {host, domain}
    for alias in aliases:
        if alias and alias not in seen and alias not in out:
            out.append(alias)
            seen.add(alias)
    return out


def _description(row: dict, robot_name: str) -> str:
    work = (row.get("work_type") or "").strip().rstrip(".")
    industries = (row.get("industries") or "").strip().replace(";", ", ")
    category = (row.get("robot_category") or "").replace("_", " ")
    bits = []
    if work:
        bits.append(work)
    if industries:
        bits.append(f"Used in {industries}")
    if not bits and category:
        bits.append(category)
    if not bits:
        return ""
    return f"{robot_name}: " + ". ".join(bits) + "."


def compile_jobs_seed() -> dict:
    seed = _load_json(SEED)
    taken = _existing_domains()
    vendors_out: list[dict] = []
    skipped = {"no_site": 0, "generic": 0, "indexed": 0, "junk": 0, "not_oem": 0}

    for row in seed.get("vendors") or []:
        if (row.get("vendor_role") or "robot_oem") != "robot_oem":
            skipped["not_oem"] += 1
            continue
        website = (row.get("website") or "").strip()
        host = host_from_website(website)
        domain = lookup_domain(website) or host
        if not website or not domain:
            skipped["no_site"] += 1
            continue
        if domain in JUNK_LOOKUP_HOSTS or host in JUNK_LOOKUP_HOSTS:
            skipped["junk"] += 1
            continue
        if domain in taken:
            skipped["indexed"] += 1
            continue
        names = split_primary_robots(row.get("primary_robots") or "", row.get("company_name") or "")
        if not names:
            skipped["generic"] += 1
            continue
        company = (row.get("company_name") or "").strip()
        primary = CATEGORY_CLASS.get(row.get("robot_category") or "", "service_robot")
        country = (row.get("country") or "").strip() or None
        robots = []
        for name in names:
            desc = _description(row, name)
            robots.append(
                {
                    "name": name,
                    "model_slug": slugify(f"{company}-{name}"),
                    "product_url": website,
                    "vendor_url": website,
                    "primary_class": primary,
                    "status": "available",
                    "country": country,
                    "description": desc,
                    "catalog_claims": [
                        {
                            "predicate": "product_class",
                            "value": primary,
                            "evidence_span": desc or f"{name} listed for {company}.",
                        }
                    ],
                    "specs": {},
                }
            )
        domains = [domain]
        if host and host not in domains:
            domains.append(host)
        for alias in _alias_domains(company, host, domain):
            if alias not in domains:
                domains.append(alias)
        vendors_out.append(
            {
                "vendor_name": company,
                "domains": domains,
                "vendor_url": website,
                "list_category": "jobs_seed",
                "robots": robots,
            }
        )
        taken.add(domain)

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "docs/calibration/robot_vendor_seed_v1.json",
        "list_category": "jobs_seed",
        "notes": [
            "FIND listing seed: robot company URL → named products (uncapped roster).",
            "FIND surfaces three robots at a time; this file is not truncated to 3.",
            "Names come from primary_robots; description from work_type/industries.",
            "Specs are omitted unless a later pass has numbers — do not invent them.",
            "Vendors already in the humanoid or commercial index are skipped.",
        ],
        "skipped": skipped,
        "vendor_count": len(vendors_out),
        "robot_count": sum(len(v["robots"]) for v in vendors_out),
        "vendors": vendors_out,
    }


def main() -> None:
    data = compile_jobs_seed()
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)} vendors={data['vendor_count']} "
        f"robots={data['robot_count']} skipped={data['skipped']}"
    )


if __name__ == "__main__":
    main()

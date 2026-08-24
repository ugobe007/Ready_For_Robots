#!/usr/bin/env python3
"""Compile the robot employment universe (placeable labor, not a tech directory).

Reads the hand-authored taxonomy (employment categories + company names),
resolves websites and up to 3 product names from existing catalogs, then
fills toward 200 OEMs that already have named robots in the vendor seed.

Never invents SKUs or specs. Category is a search lens, not a match key.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.jobs_oem_listing import (  # noqa: E402
    FIND_PRODUCT_LIST_CAP,
    split_primary_robots,
)
from app.services.vendor_robot_lookup import (  # noqa: E402
    JUNK_LOOKUP_HOSTS,
    load_vendor_robots_index,
    lookup_domain,
    lookup_vendor_by_url,
    slim_specs,
)

TAXONOMY = ROOT / "docs" / "calibration" / "robot_employment_taxonomy_v1.json"
SEED = ROOT / "docs" / "calibration" / "robot_vendor_seed_v1.json"
OUT = ROOT / "docs" / "calibration" / "robot_employment_universe_v1.json"
WORKFLOW = ROOT / "ontology" / "workflow_ontology.v1.json"

SEED_CATEGORY_TO_EMPLOYMENT = {
    "amr_agv_material_transport": "warehouse_logistics",
    "autonomous_forklift_pallet": "warehouse_logistics",
    "industrial_robot_arms": "manufacturing_machine_tending",
    "cobots": "manufacturing_machine_tending",
    "picking_manipulation_palletizing": "warehouse_logistics",
    "humanoids_general_purpose": "humanoids",
    "cleaning_robots": "commercial_cleaning",
    "hospitality_foodservice_delivery": "restaurant_hospitality",
    "inspection_security_quadrupeds": "inspection_maintenance",
    "agriculture": "agriculture",
    "construction": "construction",
    "healthcare_hospital_service": "healthcare_hospital",
    "last_mile_outdoor_delivery": "last_mile_delivery",
}

# Product-name → work family. Only names we already treat as known products.
PRODUCT_WORK_FAMILIES = {
    "fieldprinter": ["construction"],
    "stretch": ["trailer_unload"],
    "spot": ["inspect"],
    "tally": ["shelf_scan"],
    "flippy": ["food_prep"],
    "anymal": ["inspect"],
    "origin": ["transport"],
    "vector": ["transport"],
    "neo": ["scrub"],
    "relay": ["serve", "clinical_delivery"],
    "servi": ["serve"],
    "skypod": ["asrs"],
    "haipick": ["asrs"],
    "laserweeder": ["agriculture"],
    "adam": ["beverage"],
    "matradee": ["serve"],
    "chuck": ["transport"],
    "ur3e": ["gripper"],
    "ur5e": ["gripper"],
    "ur10e": ["gripper"],
}

# Official OEM sites for core taxonomy companies missing from the 500-vendor seed.
# Websites only — not product names.
KNOWN_WEBSITES = {
    "chef robotics": "https://www.chefrobotics.ai",
    "gastronomous": "https://www.gastronomous.com",
    "roboburger": "https://www.roboburger.com",
    "botrista": "https://www.botrista.com",
    "dexai": "https://www.dexai.com",
    "slip robotics": "https://www.sliprobotics.com",
    "kewazo": "https://www.kewazo.com",
    "cyphra autonomy": "https://www.cyphra.ai",
    "hyperion robotics": "https://www.hyperionrobotics.com",
    "verdant robotics": "https://www.verdantrobotics.com",
    "bluewhite": "https://www.bluewhite.ai",
    "stout industrial technology": "https://www.stoutagtech.com",
    "farm ng": "https://farm-ng.com",
    "mendaera": "https://www.mendaera.com",
    "noah medical": "https://www.noahmedical.com",
    "kinova": "https://www.kinovarobotics.com",
    "capsa healthcare": "https://www.capsahealthcare.com",
    "gecko robotics": "https://www.geckorobotics.com",
    "eddyfi technologies": "https://www.eddyfi.com",
    "robco": "https://www.robco.de",
    "standard bots": "https://standardbots.com",
    "vanderlande": "https://www.vanderlande.com",
    "whill": "https://whill.inc",
    "aerovect": "https://www.aerovect.com",
    "amp": "https://www.amprobotics.com",
    "glacier": "https://www.glacier.eco",
    "everestlabs": "https://www.everestlabs.ai",
    "zenrobotics": "https://www.zenrobotics.com",
    "recycleye": "https://www.recycleye.com",
    "waste robotics": "https://www.wasterobotics.com",
    "pronto": "https://www.pronto.ai",
    "ecoppia": "https://www.ecoppia.com",
    "airtouch solar": "https://www.airtouchsolar.com",
    "solarcleano": "https://www.solarcleano.com",
    "nauticus robotics": "https://www.nauticusrobotics.com",
    "ocean infinity": "https://oceaninfinity.com",
    "videoray": "https://www.videoray.com",
    "blue robotics": "https://bluerobotics.com",
    "cenobots": "https://www.cenobots.com",
    "sparkoz": "https://www.sparkoz.com",
    "aes": "https://www.aes.com",
    "pudu robotics": "https://www.pudurobotics.com",
    "lg electronics": "https://www.lg.com",
    "karcher": "https://www.kaercher.com",
    "deep robotics": "https://www.deeprobotics.cn",
    "rethink robotics": "https://www.rethinkrobotics.com",
    "franka robotics": "https://www.franka.de",
    "coco robotics": "https://cocodelivery.com",
    "agibot": "https://www.agibot.com",
}

NAME_ALIASES = {
    "1x": ["1x technologies"],
    "figure ai": ["figure"],
    "unitree": ["unitree robotics"],
    "ubtech": ["ubtech robotics"],
    "agibot": ["agibot (zhiyuan robotics)", "zhiyuan robotics"],
    "robotera": ["robot era"],
    "limx dynamics": ["limx"],
    "neura robotics": ["neura"],
    "fourier intelligence": ["fourier"],
    "rainbow robotics": ["rainbow"],
    "pal robotics": ["pal"],
    "mentee robotics": ["mentee"],
    "lg electronics": ["lg cloi", "lg"],
    "keenon robotics": ["keenon"],
    "pudu robotics": ["pudu"],
    "brain corp": ["brain"],
    "nilfisk": ["nilfisk liberty"],
    "kärcher": ["karcher", "karcher kira"],
    "orionstar": ["orionstar robotics"],
    "hyphen": ["hyphen foods", "hyphen robotic kitchen"],
    "picnic works": ["picnic"],
    "boston dynamics": ["boston dynamics stretch"],
    "geek+": ["geekplus", "geek plus"],
    "hai robotics": ["haipick systems"],
    "yaskawa motoman": ["yaskawa", "motoman"],
    "fanuc": ["fanuc america"],
    "abb": ["asti mobile robotics (abb)"],
    "franka robotics": ["franka emika", "franka emika industrial"],
    "standard bots": ["standard bots"],
    "techman robot": ["tm-robot", "techman"],
    "starship technologies": ["starship technologies indoor"],
    "coco robotics": ["coco delivery"],
    "caterpillar": ["caterpillar command"],
    "komatsu": ["komatsu autonomous haulage"],
    "medtronic": ["medtronic hugo / mazor"],
    "stryker": ["stryker mako"],
    "intuitive surgical": ["intuitive"],
    "cmr surgical": ["cmr"],
    "zimmer biomet": ["zimmer biomet rosa"],
    "deep robotics": ["deeprobotics"],
    "anybotics": ["anybotics"],
    "ghost robotics": ["ghost"],
    "farm-ng": ["farmng", "farm ng"],
    "naïo technologies": ["naio technologies", "naio"],
    "aes": ["aes/maximo"],
    "amp": ["amp robotics"],
    "glacier": ["glacier robotics"],
    "pronto": ["pronto.ai"],
    "safeai": ["safe ai"],
    "fbr": ["fastbrick robotics", "fbr.com.au"],
    "okibo": ["okibo"],
    "canvas": ["canvas.build"],
    "construction robotics": ["construction sam"],
    "advanced construction robotics": ["advanced construction robotics"],
    "relay robotics": ["savioke relay", "savioke"],
    "whill": ["whill"],
    "vanderlande": ["vanderlande"],
    "greensea iq": ["greensea"],
    "blue robotics": ["bluerobotics"],
    "nauticus robotics": ["nauticus"],
    "waste robotics": ["waste robotics"],
    "zenrobotics": ["zenrobotics"],
    "everestlabs": ["everest labs"],
    "recycleye": ["recycleye"],
    "airtouch solar": ["airtouch"],
    "solarcleano": ["solarcleano"],
    "ecoppia": ["ecoppia"],
    "eddyfi technologies": ["eddyfi"],
    "energy robotics": ["energy robotics"],
    "capsa healthcare": ["capsa"],
    "kinova": ["kinova"],
    "mendaera": ["mendaera"],
    "noah medical": ["noah"],
    "moon surgical": ["moon surgical"],
    "slip robotics": ["slip"],
    "brightpick": ["brightpick"],
    "pickle robot": ["pickle"],
    "dexterity": ["dexterity"],
    "righthand robotics": ["right hand robotics", "righthand"],
    "mujin": ["mujin"],
    "exotec": ["exotec"],
    "seegrid": ["seegrid"],
    "vecna robotics": ["vecna"],
    "locus robotics": ["locus"],
    "chef robotics": ["chef robotics"],
    "gastronomous": ["gastronomous"],
    "roboburger": ["roboburger"],
    "botrista": ["botrista"],
    "dexai": ["dexai"],
    "cenobots": ["cenobots"],
    "sparkoz": ["sparkoz"],
    "cleanfix": ["cleanfix"],
    "tennant": ["tennant"],
    "gausium": ["gausium"],
    "lionsbot": ["lionsbot"],
    "avidbots": ["avidbots"],
    "bear robotics": ["bear"],
    "richtech robotics": ["richtech"],
    "simbe robotics": ["simbe"],
    "badger technologies": ["badger"],
    "serve robotics": ["serve"],
    "cartken": ["cartken"],
    "ottonomy": ["ottonomy"],
    "nuro": ["nuro"],
    "aurrigo": ["aurrigo"],
    "aerovect": ["aerovect"],
    "cyphra autonomy": ["cyphra"],
    "hyperion robotics": ["hyperion"],
    "kewazo": ["kewazo"],
    "built robotics": ["built"],
    "dusty robotics": ["dusty"],
    "carbon robotics": ["carbon"],
    "farmwise": ["farmwise"],
    "burro": ["burro"],
    "verdant robotics": ["verdant"],
    "bluewhite": ["bluewhite"],
    "stout industrial technology": ["stout"],
    "harvest croo": ["harvest croo"],
    "tortuga agtech": ["tortuga"],
    "saga robotics": ["saga"],
    "diligent robotics": ["diligent"],
    "gecko robotics": ["gecko"],
    "flyability": ["flyability"],
    "knightscope": ["knightscope"],
    "cobalt robotics": ["cobalt"],
    "smp robotics": ["smp"],
    "robco": ["robco"],
    "universal robots": ["universal robots"],
    "kuka": ["kuka"],
    "doosan robotics": ["doosan"],
    "rethink robotics": ["rethink robotics (original sawyer legacy)"],
    "ocean infinity": ["ocean infinity"],
    "videoray": ["videoray"],
}


def _norm(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.replace("ä", "a").replace("ï", "i").replace("+", "plus")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(
        r"\b(inc|llc|ltd|gmbh|corp|co|ag|plc|robotics|robot|the)\b",
        " ",
        t,
    )
    return re.sub(r"\s+", " ", t).strip()


def _site_key(text: str) -> str:
    """Stable lookup key that keeps 'robotics' so Chef Robotics ≠ Chef."""
    t = (text or "").strip().lower()
    t = t.replace("ä", "a").replace("ï", "i").replace("+", "plus")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _workflow_family_ids() -> set[str]:
    data = _load(WORKFLOW)
    return set((data.get("families") or {}).keys())


def _entry_name(raw: str | dict[str, Any]) -> tuple[str, str | None]:
    if isinstance(raw, dict):
        return str(raw.get("name") or "").strip(), (raw.get("product_hint") or None)
    return str(raw).strip(), None


def _alias_keys(name: str) -> set[str]:
    key = _norm(name)
    out = {key}
    for extra in NAME_ALIASES.get(key, []):
        out.add(_norm(extra))
    return {k for k in out if k}


def _index_seed(seed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for vendor in seed.get("vendors") or []:
        name = vendor.get("company_name") or ""
        for key in _alias_keys(name):
            existing = by_key.get(key)
            if existing is None or len(vendor.get("primary_robots") or "") > len(
                existing.get("primary_robots") or ""
            ):
                by_key[key] = vendor
    return by_key


def _robots_from_catalog(website: str, hint: str | None) -> list[dict[str, Any]]:
    vendor = lookup_vendor_by_url(website) if website else None
    rows = list((vendor or {}).get("robots") or [])
    names: list[dict[str, Any]] = []
    hint_key = _norm(hint or "")
    if hint_key:
        for robot in rows:
            name = (robot.get("name") or "").strip()
            if hint_key and hint_key in _norm(name):
                names.append(_robot_row(robot, source="vendor_index", hint=hint))
                break
    for robot in rows:
        name = (robot.get("name") or "").strip()
        if not name:
            continue
        if any(_norm(name) == _norm(r["name"]) for r in names):
            continue
        names.append(_robot_row(robot, source="vendor_index", hint=None))
        if len(names) >= FIND_PRODUCT_LIST_CAP:
            break
    return names[:FIND_PRODUCT_LIST_CAP]


def _robots_from_seed(vendor: dict[str, Any], hint: str | None) -> list[dict[str, Any]]:
    company = vendor.get("company_name") or ""
    names = split_primary_robots(vendor.get("primary_robots") or "", company)
    if hint:
        hinted = [n for n in names if _norm(hint) in _norm(n)]
        rest = [n for n in names if n not in hinted]
        names = hinted + rest
    class_value = SEED_CATEGORY_TO_EMPLOYMENT.get(vendor.get("robot_category") or "", "")
    out: list[dict[str, Any]] = []
    for name in names[:FIND_PRODUCT_LIST_CAP]:
        out.append(
            {
                "name": name,
                "robot_class": vendor.get("robot_category") or class_value or None,
                "work_families": _families_for_product(name),
                "name_source": "vendor_seed",
                "capabilities_epistemic": "unknown",
                "specs": {},
            }
        )
    return out


def _robot_row(robot: dict[str, Any], *, source: str, hint: str | None) -> dict[str, Any]:
    name = (robot.get("name") or "").strip()
    specs = slim_specs(robot.get("specs") or {})
    return {
        "name": name,
        "robot_class": robot.get("primary_class") or None,
        "work_families": _families_for_product(name),
        "name_source": source,
        "capabilities_epistemic": "explicit" if specs else "unknown",
        "specs": specs,
        "product_url": robot.get("product_url") or None,
        "product_hint": hint,
    }


def _families_for_product(name: str) -> list[str]:
    key = _norm(name).replace(" ", "")
    for token, families in PRODUCT_WORK_FAMILIES.items():
        if token in key or key in token:
            return list(families)
    return []


def _match_seed(name: str, by_key: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    for key in _alias_keys(name):
        hit = by_key.get(key)
        if hit:
            return hit
    want = set(_norm(name).split())
    if len(want) < 2:
        return None
    best = None
    best_score = 0
    for key, vendor in by_key.items():
        have = set(key.split())
        score = len(want & have)
        # Require the distinctive first token, so "Blue Robotics" ≠ Blue Ocean.
        if want and list(want)[0] not in have and _norm(name).split()[0] not in have:
            continue
        if score >= 2 and score > best_score:
            # Prefer the shorter vendor name (Pudu over Pudu CC1).
            if best and len(vendor.get("company_name") or "") > len(best.get("company_name") or ""):
                continue
            best = vendor
            best_score = score
    return best


def compile_universe() -> dict[str, Any]:
    taxonomy = _load(TAXONOMY)
    seed = _load(SEED)
    by_key = _index_seed(seed)
    family_ids = _workflow_family_ids()
    load_vendor_robots_index()

    companies: dict[str, dict[str, Any]] = {}
    core_names: list[tuple[str, str | None, str]] = []
    for cat in taxonomy.get("employment_categories") or []:
        cat_id = cat["id"]
        for raw in cat.get("companies") or []:
            name, hint = _entry_name(raw)
            if name:
                core_names.append((name, hint, cat_id))

    unresolved: list[dict[str, Any]] = []
    for name, hint, cat_id in core_names:
        slug = _norm(name)
        row = companies.get(slug)
        if row is None:
            vendor = _match_seed(name, by_key)
            website = (
                KNOWN_WEBSITES.get(_site_key(name))
                or KNOWN_WEBSITES.get(_norm(name))
                or (vendor or {}).get("website")
                or ""
            )
            domain = lookup_domain(website) if website else ""
            if domain in JUNK_LOOKUP_HOSTS:
                website, domain = "", ""
            robots = []
            if website:
                robots = _robots_from_catalog(website, hint)
            if not robots and vendor:
                robots = _robots_from_seed(vendor, hint)
            row = {
                "company_name": name,
                "matched_seed_name": (vendor or {}).get("company_name") or None,
                "taxonomy_name": name,
                "website": website or None,
                "country": (vendor or {}).get("country") or None,
                "vendor_role": (vendor or {}).get("vendor_role") or "robot_oem",
                "commercial_maturity": (vendor or {}).get("commercial_maturity") or "unknown",
                "us_availability": (vendor or {}).get("us_availability") or None,
                "employment_categories": [],
                "priority": "core",
                "robots": robots,
                "resolved": bool(website and robots),
            }
            companies[slug] = row
            if not website or not robots:
                unresolved.append(
                    {
                        "company_name": name,
                        "website": website or None,
                        "missing": "website" if not website else "named_robots",
                    }
                )
        if cat_id not in row["employment_categories"]:
            row["employment_categories"].append(cat_id)
        if hint and row["robots"]:
            # Prefer hinted SKU first.
            hinted = [r for r in row["robots"] if hint.lower() in r["name"].lower()]
            rest = [r for r in row["robots"] if r not in hinted]
            row["robots"] = (hinted + rest)[:FIND_PRODUCT_LIST_CAP]

    # Fill toward 200 from seed OEMs that already have named robots.
    taken_hosts = {
        lookup_domain(c["website"]) for c in companies.values() if c.get("website")
    }
    taken_names = {_norm(c["company_name"]) for c in companies.values()}
    fillers: list[dict[str, Any]] = []
    for vendor in seed.get("vendors") or []:
        if (vendor.get("vendor_role") or "robot_oem") != "robot_oem":
            continue
        website = (vendor.get("website") or "").strip()
        domain = lookup_domain(website) if website else ""
        if not domain or domain in JUNK_LOOKUP_HOSTS or domain in taken_hosts:
            continue
        name = vendor.get("company_name") or ""
        if _norm(name) in taken_names:
            continue
        robots = _robots_from_catalog(website, None) or _robots_from_seed(vendor, None)
        if not robots:
            continue
        emp = SEED_CATEGORY_TO_EMPLOYMENT.get(vendor.get("robot_category") or "")
        if not emp:
            continue
        maturity = vendor.get("commercial_maturity") or "unknown"
        us = (vendor.get("us_availability") or "").lower()
        score = len(robots) * 10
        if maturity in {"commercial", "production"}:
            score += 5
        if us in {"yes", "true", "us"}:
            score += 3
        fillers.append(
            {
                "score": score,
                "row": {
                    "company_name": name,
                    "taxonomy_name": name,
                    "website": website,
                    "country": vendor.get("country") or None,
                    "vendor_role": "robot_oem",
                    "commercial_maturity": maturity,
                    "us_availability": vendor.get("us_availability") or None,
                    "employment_categories": [emp],
                    "priority": "fill",
                    "robots": robots,
                    "resolved": True,
                    "matched_seed_name": name,
                },
            }
        )
    fillers.sort(key=lambda x: -x["score"])
    target = int(taxonomy.get("target_companies") or 200)
    for item in fillers:
        if len(companies) >= target:
            break
        row = item["row"]
        slug = _norm(row["company_name"])
        if slug in companies:
            continue
        companies[slug] = row
        taken_hosts.add(lookup_domain(row["website"]))

    # Drop illegal work families.
    for row in companies.values():
        for robot in row["robots"]:
            robot["work_families"] = [
                f for f in robot.get("work_families") or [] if f in family_ids
            ]

    ordered = sorted(
        companies.values(),
        key=lambda c: (0 if c["priority"] == "core" else 1, c["company_name"].lower()),
    )
    named_robot_count = sum(len(c["robots"]) for c in ordered)
    with_three = sum(1 for c in ordered if len(c["robots"]) >= 3)
    core = sum(1 for c in ordered if c["priority"] == "core")

    return {
        "dataset_id": "robot_employment_universe_v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "docs/calibration/robot_employment_taxonomy_v1.json",
        "purpose": taxonomy.get("purpose"),
        "north_star": taxonomy.get("north_star"),
        "spine": taxonomy.get("spine"),
        "rule": taxonomy.get("rule"),
        "target_companies": target,
        "company_count": len(ordered),
        "core_company_count": core,
        "named_robot_count": named_robot_count,
        "companies_with_three_robots": with_three,
        "unresolved_core": unresolved,
        "notes": [
            "Core companies come from the employment taxonomy (placeable labor).",
            "Fill companies are existing seed OEMs that already have named robots.",
            "Robot names are copied from vendor indexes / primary_robots only.",
            "Empty robots[] means the OEM site names are not in our catalog yet — do not invent them.",
            "work_families are product-level search lenses from known SKUs, not category leakage.",
            "jobs_rfr_can_find is the FIND matcher output at query time, not a stored list.",
        ],
        "employment_categories": [
            {"id": c["id"], "label": c["label"]}
            for c in taxonomy.get("employment_categories") or []
        ],
        "companies": ordered,
    }


def main() -> None:
    data = compile_universe()
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)} companies={data['company_count']} "
        f"core={data['core_company_count']} robots={data['named_robot_count']} "
        f"unresolved={len(data['unresolved_core'])} "
        f"with_3={data['companies_with_three_robots']}"
    )


if __name__ == "__main__":
    main()

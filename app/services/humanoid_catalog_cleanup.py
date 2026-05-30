"""
Prune duplicate humanoid benchmark rows and buyer-site pilot projects.

Also drops RSS headline junk and vendor-only placeholder rows re-imported from
``robot_companies`` or news discovery.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_scraper import _normalize_vendor

# One flagship SKU per vendor on the leaderboard.
CANONICAL_SLUG_BY_VENDOR: Dict[str, str] = {
    "unitree": "unitree-g1",
    "figure ai": "figure-02",
    "boston dynamics": "boston-dynamics-atlas",
    "agility robotics": "agility-digit",
    "tesla": "tesla-optimus-gen2",
    "apptronik": "apptronik-apollo",
    "1x technologies": "1x-neo",
    "sanctuary ai": "sanctuary-phoenix",
    "agibot": "agibot-a2",
    "ubtech robotics": "ubtech-walker-x",
    "engineai": "engineai-pm01",
    "fourier intelligence": "fourier-gr1",
    "xpeng robotics": "xpeng-px5",
    "leju robotics": "leju-kuavo",
    "neura robotics": "neura-4ne1",
    "pal robotics": "pal-talos",
    "engineered arts": "engineered-arts-ameca",
    "reflex robotics": "reflex-humanoid",
    "mentee robotics": "mentee-bot",
    "persona ai": "persona-ai-gen1",
    "dlr": "dlr-toro",
    "astribot": "astribot-s1",
    "galbot": "galbot-g1",
    "robotera": "robotera-star1",
    "limx dynamics": "limx-tron1",
    "kepler exploration robotics": "kepler-k2",
    "booster robotics": "booster-t1",
    "pndbotics": "pndbotics-adam",
    "noetix robotics": "noetix-n2",
    "xiaomi": "xiaomi-cyberone",
    "toyota": "toyota-thr3",
    "honda": "honda-asimo-successor",
    "rainbow robotics": "rainbow-hubo",
    "preferred networks": "pfn-humanoid",
    "clone robotics": "clone-alpha",
    "shadow robot company": "shadow-hand-platform",
    "nasa johnson": "nasa-valkyrie",
    "kawasaki robotics": "kawasaki-kaleido",
    "softbank robotics": "softbank-pepper-next",
    "samsung research": "samsung-bot-handy",
    "lg electronics": "lg-cloi-suitbot",
    "cloudminds": "cloudminds-ginger-xr",
    "chery robotics": "chery-mornine",
    "skild ai": "skild-humanoid-stack",
    "physical intelligence": "pi-humanoid-research",
    "covariant": "covariant-humanoid",
    "openai robotics": "openai-humanoid-partner",
    "meta fair": "meta-fair-humanoid",
    "google deepmind": "deepmind-humanoid",
    "waymo": "waymo-humanoid",
    "apple robotics": "apple-humanoid",
    "microsoft robotics": "microsoft-humanoid",
    "intel labs": "intel-humanoid",
    "qualcomm": "qualcomm-humanoid",
    "amd": "amd-humanoid",
    "arm robotics": "arm-humanoid",
    "siemens": "siemens-humanoid",
    "abb robotics": "abb-humanoid",
    "fanuc": "fanuc-humanoid",
    "kuka": "kuka-humanoid",
    "yaskawa": "yaskawa-humanoid",
    "universal robots": "ur-humanoid",
    "techman robot": "techman-humanoid",
    "doosan robotics": "doosan-humanoid",
    "franka emika": "franka-humanoid",
    "comau": "comau-humanoid",
    "epson robotics": "epson-humanoid",
    "omron robotics": "omron-humanoid",
    "mitsubishi electric": "mitsubishi-humanoid",
    "denso robotics": "denso-humanoid",
    "nidec robotics": "nidec-humanoid",
    "harmonic drive": "harmonic-humanoid",
    "maxon group": "maxon-humanoid-kit",
}

# Buyer deployment pilots — not distinct robot products.
DEPLOYMENT_PILOT_SLUGS: Set[str] = {
    "amazon-digit",
    "bmw-apptronik",
    "bmw-figure",
    "bmw-figure-pilot",
    "foxconn-optimus",
    "foxconn-unitree",
    "gxo-digit",
    "hyundai-atlas",
    "mercedes-apptronik",
    "mercedes-figure",
    "schaeffler-4ne1",
    "siemens-humanoid",
}

# Older variants / merged vendors — keep flagship SKU per line.
DUPLICATE_PRODUCT_SLUGS: Set[str] = {
    "1x-neo-beta",
    "agility-digit-2",
    "apptronik-a2",
    "astribot-s2",
    "booster-k1",
    "engineai-sa01",
    "engineai-t800",
    "figure-01",
    "figure-03",
    "fourier-gr2",
    "fourier-n1",
    "galbot-g2",
    "halodi-eve",
    "ihmc-atlas",
    "kepler-k1",
    "leju-kuavo-3",
    "limx-oli",
    "mentee-bot-pro",
    "neura-maira",
    "noetix-e1",
    "pal-ari",
    "pal-reem-c",
    "pndbotics-adam-u",
    "persona-ai-gen2",
    "reflex-gen2",
    "robotera-star2",
    "sanctuary-m-series",
    "tesla-optimus-gen1",
    "xiaomi-cyberone-pro",
    "zhiyuan-lingxi",
}

# Generic rows from robot_companies bridge ({Company} Humanoid).
VENDOR_PLACEHOLDER_SLUGS: Set[str] = {
    "agibot",
    "apptronik",
    "boston-dynamics",
    "engineai",
    "figure-ai",
    "leju-robotics",
    "unitree",
    "unitree-robotics",
    "zhiyuan-robotics",
}

# Speculative / non-product catalog slugs (not real humanoid SKUs).
SPECULATIVE_CATALOG_SLUGS: Set[str] = {
    "abb-humanoid",
    "alibaba-humanoid",
    "amd-humanoid",
    "apple-humanoid",
    "arm-humanoid",
    "baidu-humanoid",
    "byd-humanoid",
    "bytedance-humanoid",
    "cainiao-humanoid",
    "cloudwalk-humanoid",
    "comau-humanoid",
    "covariant-humanoid",
    "deepmind-humanoid",
    "denso-humanoid",
    "dji-humanoid",
    "doosan-humanoid",
    "dreame-humanoid",
    "ecovacs-humanoid",
    "epson-humanoid",
    "fanuc-humanoid",
    "forwardx-humanoid",
    "franka-humanoid",
    "geekplus-humanoid",
    "geely-humanoid",
    "hai-humanoid",
    "haier-humanoid",
    "hans-humanoid",
    "harmonic-humanoid",
    "hit-humanoid",
    "horizon-humanoid",
    "huawei-humanoid",
    "iflytek-humanoid",
    "intel-humanoid",
    "jaka-humanoid",
    "jd-humanoid",
    "kuka-humanoid",
    "liauto-humanoid",
    "maxon-humanoid-kit",
    "megvii-humanoid",
    "meituan-humanoid",
    "meta-fair-humanoid",
    "microsoft-humanoid",
    "mitsubishi-humanoid",
    "nidec-humanoid",
    "ninebot-humanoid",
    "nio-humanoid",
    "nvidia-gr00t-humanoid",
    "omron-humanoid",
    "openai-humanoid-partner",
    "pi-humanoid-research",
    "qualcomm-humanoid",
    "quicktron-humanoid",
    "sensetime-humanoid",
    "sf-humanoid",
    "skild-humanoid-stack",
    "standard-robots-humanoid",
    "techman-humanoid",
    "tencent-humanoid",
    "ur-humanoid",
    "visionnav-humanoid",
    "waymo-humanoid",
    "yaskawa-humanoid",
    "youibot-humanoid",
    "zte-humanoid",
}

NEWS_JUNK_RE = re.compile(
    r"(coolest things|captivate crowds|pavilion humanoid|debut unmanned|"
    r"humanoid robots humanoid|robot pavilion|to debut unmanned)",
    re.I,
)

GENERIC_SUFFIX_RE = re.compile(
    r"\b(humanoid research|humanoid platform|humanoid stack|humanoid lab|"
    r"humanoid partner|humanoid pilot)\b",
    re.I,
)


def is_excluded_humanoid_slug(slug: str) -> bool:
    s = (slug or "").strip().lower()
    if not s:
        return True
    return (
        s in DEPLOYMENT_PILOT_SLUGS
        or s in DUPLICATE_PRODUCT_SLUGS
        or s in VENDOR_PLACEHOLDER_SLUGS
        or s in SPECULATIVE_CATALOG_SLUGS
    )


def is_junk_humanoid_row(name: str, vendor: str, model_slug: str) -> bool:
    slug = (model_slug or "").strip().lower()
    n = (name or "").strip()
    v = (vendor or "").strip()

    if is_excluded_humanoid_slug(slug):
        return True

    blob = f"{n} {v} {slug}"
    if NEWS_JUNK_RE.search(blob):
        return True

    if GENERIC_SUFFIX_RE.search(n) and slug.endswith("-humanoid"):
        return True

    # "{Vendor} Humanoid" placeholder (incl. robot_companies + RSS)
    if n.lower().endswith(" humanoid"):
        base = n[:-9].strip().lower()
        if base == v.lower() or base == _normalize_vendor(v):
            return True
        if len(v) > 36 or len(base) > 36:
            return True

    return False


def vendor_key(vendor: str) -> str:
    return _normalize_vendor(vendor or "")


def canonical_slug_for_vendor(vendor: str, rows: List[dict]) -> str:
    """Pick the single row to keep for a vendor."""
    key = vendor_key(vendor)
    preferred = CANONICAL_SLUG_BY_VENDOR.get(key)
    slugs = {r.get("model_slug") for r in rows}
    if preferred and preferred in slugs:
        return preferred
    if preferred:
        return preferred

    def sort_key(row: dict):
        heif = float(row.get("heif_total") or 0)
        score = float(row.get("score_total") or 0)
        return (-heif, -score, row.get("model_slug") or "")

    return sorted(rows, key=sort_key)[0]["model_slug"]


def vendor_duplicate_rows(rows: List[dict]) -> List[dict]:
    """Return non-canonical rows to delete (one entry per vendor)."""
    by_vendor: Dict[str, List[dict]] = {}
    for row in rows:
        key = vendor_key(row.get("vendor") or "")
        if not key:
            continue
        by_vendor.setdefault(key, []).append(row)

    to_delete: List[dict] = []
    for group in by_vendor.values():
        if len(group) <= 1:
            continue
        keep_slug = canonical_slug_for_vendor(group[0].get("vendor") or "", group)
        for row in group:
            if row.get("model_slug") != keep_slug:
                to_delete.append(row)
    return to_delete


def cleanup_humanoid_benchmarks(db: Session, *, dry_run: bool = False) -> Dict[str, Any]:
    rows = db.execute(
        text("""
            SELECT id, model_slug, name, vendor, heif_total, score_total
            FROM humanoid_benchmarks ORDER BY id
        """)
    ).mappings().all()
    row_dicts = [dict(r) for r in rows]

    junk = [r for r in row_dicts if is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])]
    junk_ids = {r["id"] for r in junk}
    survivors = [r for r in row_dicts if r["id"] not in junk_ids]
    vendor_dupes = vendor_duplicate_rows(survivors)

    to_delete = junk + vendor_dupes
    dupe_slugs = {r["model_slug"] for r in vendor_dupes}

    if not dry_run and to_delete:
        for row in to_delete:
            db.execute(
                text("DELETE FROM humanoid_benchmarks WHERE id = :id"),
                {"id": row["id"]},
            )
        db.commit()

    return {
        "dry_run": dry_run,
        "scanned": len(rows),
        "removed": len(to_delete),
        "removed_junk": len(junk),
        "removed_vendor_duplicates": len(vendor_dupes),
        "remaining": len(rows) - len(to_delete),
        "removed_slugs": [r["model_slug"] for r in to_delete],
        "vendor_duplicate_slugs": sorted(dupe_slugs),
    }

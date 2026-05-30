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

# Same robot imported twice under a renamed slug (not a distinct product version).
SAME_ROBOT_DUPLICATE_SLUGS: Set[str] = {
    "1x-neo-beta",
    "halodi-eve",
    "ihmc-atlas",
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
        or s in SAME_ROBOT_DUPLICATE_SLUGS
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

    # "Figure Humanoid" / "Figure AI Humanoid" — generic vendor label, not a model SKU.
    if re.match(r"^figure(\s+ai)?\s+humanoid$", n, re.I):
        return True

    return False


def vendor_key(vendor: str) -> str:
    return _normalize_vendor(vendor or "")


def _has_distinct_model_identity(name: str, vendor: str, model_slug: str) -> bool:
    """True when the row names a specific product SKU, not a vendor placeholder."""
    if is_junk_humanoid_row(name, vendor, model_slug):
        return False
    slug = (model_slug or "").strip().lower()
    if slug in VENDOR_PLACEHOLDER_SLUGS or slug in SAME_ROBOT_DUPLICATE_SLUGS:
        return False
    if re.search(r"\d", slug) or re.search(r"\d", name or ""):
        return True

    vendor_slug = re.sub(r"[^a-z0-9]+", "-", _normalize_vendor(vendor)).strip("-")
    if slug in (vendor_slug, f"{vendor_slug}-humanoid"):
        return False

    # Named products without digits (Atlas, Digit, G1-style slugs, reflex-humanoid, etc.)
    return "-" in slug and slug not in SPECULATIVE_CATALOG_SLUGS


def vendor_duplicate_rows(rows: List[dict]) -> List[dict]:
    """Drop generic vendor placeholders when the same company has named model rows."""
    by_vendor: Dict[str, List[dict]] = {}
    for row in rows:
        key = vendor_key(row.get("vendor") or "")
        if not key:
            continue
        by_vendor.setdefault(key, []).append(row)

    to_delete: List[dict] = []
    for group in by_vendor.values():
        products = [
            r
            for r in group
            if _has_distinct_model_identity(r["name"], r["vendor"], r["model_slug"])
        ]
        if not products:
            continue
        for row in group:
            if not _has_distinct_model_identity(row["name"], row["vendor"], row["model_slug"]):
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

    deleted: List[dict] = []
    failed: List[dict] = []
    if not dry_run and to_delete:
        for row in to_delete:
            try:
                db.execute(
                    text("DELETE FROM humanoid_benchmarks WHERE id = :id"),
                    {"id": row["id"]},
                )
                db.commit()
                deleted.append(row)
            except Exception:
                db.rollback()
                failed.append(row)

    removed = junk + deleted if not dry_run else to_delete

    return {
        "dry_run": dry_run,
        "scanned": len(rows),
        "removed": len(removed),
        "removed_junk": len(junk),
        "removed_vendor_duplicates": len(vendor_dupes),
        "deleted": len(deleted),
        "failed": len(failed),
        "remaining": len(rows) - len(removed),
        "removed_slugs": [r["model_slug"] for r in removed],
        "failed_slugs": [r["model_slug"] for r in failed],
        "vendor_duplicate_slugs": sorted(dupe_slugs),
    }

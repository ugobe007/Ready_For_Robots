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


def cleanup_humanoid_benchmarks(db: Session, *, dry_run: bool = False) -> Dict[str, Any]:
    rows = db.execute(
        text("SELECT id, model_slug, name, vendor FROM humanoid_benchmarks ORDER BY id")
    ).mappings().all()

    to_delete: List[dict] = []
    for row in rows:
        if is_junk_humanoid_row(row["name"], row["vendor"], row["model_slug"]):
            to_delete.append(dict(row))

    if not dry_run and to_delete:
        ids = [r["id"] for r in to_delete]
        db.execute(
            text("DELETE FROM humanoid_benchmarks WHERE id = ANY(:ids)"),
            {"ids": ids},
        )
        db.commit()

    return {
        "dry_run": dry_run,
        "scanned": len(rows),
        "removed": len(to_delete),
        "remaining": len(rows) - len(to_delete),
        "removed_slugs": [r["model_slug"] for r in to_delete],
    }

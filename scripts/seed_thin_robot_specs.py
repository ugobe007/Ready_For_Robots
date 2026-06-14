"""
Apply curated datasheet specs from HUMANOID_CATALOG into humanoid_benchmarks
and rescore. The normal catalog sync pushes identity/entity fields but NOT the
`specs` JSON, so this merges catalog specs (catalog datasheet wins for the keys
it provides), recomputes HEIF, and writes the score columns that exist.

Also runs sync_product_urls_from_catalog so Chinese names / aliases land too.

Usage (on the app box):
    python scripts/seed_thin_robot_specs.py
"""
from __future__ import annotations

import json

from sqlalchemy import text

from app.database import SessionLocal
from app.services.humanoid_scraper import compute_scores
from app.services.humanoid_vendor_catalog import (
    catalog_entries,
    sync_product_urls_from_catalog,
)

# Slugs whose catalog `specs` should be merged + rescored. Entries with only
# note-style specs (no scoreable fields) are skipped automatically.
TARGETS = {
    "ti5-yaoguang", "ubtech-walker-s", "xpeng-iron", "fourier-n1",
    "kepler-k1", "kawasaki-kaleido",
}


def main() -> None:
    db = SessionLocal()
    try:
        sres = sync_product_urls_from_catalog(db)
        print("SYNC", json.dumps(sres))

        cols = {
            r[0] for r in db.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='humanoid_benchmarks'"
            )).all()
        }
        cat = {e["model_slug"]: e for e in catalog_entries()}
        for slug in sorted(TARGETS):
            entry = cat.get(slug)
            if not entry:
                print("MISSING", slug)
                continue
            cat_specs = entry.get("specs") or {}
            if not cat_specs:
                print("NOSPEC", slug)
                continue
            row = db.execute(text(
                "SELECT specs, status, vendor FROM humanoid_benchmarks "
                "WHERE model_slug = :s"
            ), {"s": slug}).mappings().first()
            if not row:
                print("NOROW", slug)
                continue
            cur = row["specs"] or {}
            if isinstance(cur, str):
                cur = json.loads(cur)
            merged = dict(cur)
            merged.update(cat_specs)  # curated datasheet wins
            scores = compute_scores(
                merged, status=row["status"] or "research",
                vendor=row["vendor"] or "",
            )
            set_parts = ["specs = cast(:specs as jsonb)"]
            params = {"specs": json.dumps(merged), "s": slug}
            for k, v in scores.items():
                if k in cols:
                    set_parts.append(f"{k} = :{k}")
                    params[k] = v
            if "updated_at" in cols:
                set_parts.append("updated_at = NOW()")
            db.execute(text(
                f"UPDATE humanoid_benchmarks SET {', '.join(set_parts)} "
                "WHERE model_slug = :s"
            ), params)
            print(f"OK {slug:18s} dof={merged.get('total_dof')} "
                  f"h={merged.get('height_cm')} w={merged.get('weight_kg')} "
                  f"payload={merged.get('payload_kg')} torque={merged.get('peak_torque_nm')} "
                  f"heif={scores.get('heif_total')} score={scores.get('score_total')}")
        db.commit()
        print("MERGE_DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
One-shot apply of fetch-verified specs for Fourier GR-1 and GR-2.

Each value below was extracted strictly from the vendor's dedicated product
page (fftai.com) during the fetch-and-verify dry run, with a verbatim quote.
Only fills fields that are currently missing; recomputes HEIF + rule scores;
records provenance in `sources`. Designed to run on the Fly machine where
DATABASE_URL is configured.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.services.humanoid_scraper import compute_scores  # noqa: E402
from app.services.humanoid_ai_stack import scoring_specs, specs_for_storage  # noqa: E402

VERIFIED = {
    "fourier-gr1": {
        "source": "https://www.fftai.com/products-gr1",
        "specs": {
            "height_cm": 165,
            "weight_kg": 55,
            "top_speed_mps": 1.39,
            "peak_torque_nm": 230,
        },
        "quotes": {
            "height_cm": "Height 165 cm",
            "weight_kg": "Weight 55 kg",
            "top_speed_mps": "Speed 5 km/hr",
            "peak_torque_nm": "Max. peak torque 230 N.m",
        },
    },
    "fourier-gr2": {
        "source": "https://www.fftai.com/products-gr2",
        "specs": {
            "height_cm": 175,
            "weight_kg": 63,
            "battery_life_h": 2,
            "top_speed_mps": 1.39,
            "peak_torque_nm": 380,
            "has_dexterous_hands": True,
            "has_sdk": True,
            "has_api": True,
        },
        "quotes": {
            "height_cm": "Height 175 cm",
            "weight_kg": "Weight 63 kg",
            "battery_life_h": "Battery 2 hours",
            "top_speed_mps": "Speed 5 km/h",
            "peak_torque_nm": "Peak Torques 380 N.m",
            "has_dexterous_hands": "GR-2 introduces 12-DoF dexterous hands",
            "has_sdk": "The upgraded Software Development Kit allows developers easy access",
            "has_api": "robust suite of pre-optimized modules via intuitive APIs",
        },
    },
}


def main() -> None:
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        for slug, payload in VERIFIED.items():
            row = db.execute(
                text("SELECT name, vendor, status, specs, sources, score_total, heif_total "
                     "FROM humanoid_benchmarks WHERE model_slug = :s"),
                {"s": slug},
            ).mappings().first()
            if not row:
                print(f"  {slug}: NOT FOUND")
                continue
            existing = dict(row["specs"] or {})
            merge = {
                k: v for k, v in payload["specs"].items()
                if existing.get(k) in (None, "")
            }
            if not merge:
                print(f"  {slug}: nothing to fill (already populated)")
                continue
            merged = specs_for_storage({**existing, **merge}, slug)
            scores = compute_scores(scoring_specs(merged), status=row["status"], vendor=row["vendor"])
            prov = list(row["sources"] or []) + [{
                "url": payload["source"],
                "scraped_at": now.isoformat(),
                "method": "fetch_verify",
                "fields": list(merge.keys()),
                "quotes": {k: payload["quotes"].get(k) for k in merge},
            }]
            db.execute(
                text(
                    "UPDATE humanoid_benchmarks SET specs = cast(:specs as jsonb), "
                    "sources = cast(:sources as jsonb), last_scraped_at = :now, updated_at = :now, "
                    "score_mobility=:score_mobility, score_manipulation=:score_manipulation, "
                    "score_autonomy=:score_autonomy, score_safety=:score_safety, "
                    "score_endurance=:score_endurance, score_market_readiness=:score_market_readiness, "
                    "score_total=:score_total, heif_mobility=:heif_mobility, heif_manipulation=:heif_manipulation, "
                    "heif_cognition=:heif_cognition, heif_safety=:heif_safety, heif_data_pipeline=:heif_data_pipeline, "
                    "heif_production=:heif_production, heif_total=:heif_total WHERE model_slug = :slug"
                ),
                {"specs": json.dumps(merged), "sources": json.dumps(prov[-30:]),
                 "now": now, "slug": slug, **scores},
            )
            db.commit()
            print(f"  {slug}: filled {list(merge.keys())}")
            print(f"     score_total {row['score_total']} -> {scores['score_total']}  "
                  f"heif_total {row['heif_total']} -> {scores['heif_total']}")
        print("DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Local preview of robot URL -> prompt v4 -> buyer opportunities.

Uses saved pages and a buyer CSV. Writes mappings into a temporary SQLite
file, then reads that new table back. Does not open the production database
and does not update any existing table.

TAXONOMY_MATCH_ENABLED stays off. This script calls the flagged composer directly.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.company import Company
from app.models.company_taxonomy_industry import CompanyTaxonomyIndustry
from app.services.taxonomy_buyer_match import readiness_from_signals
from app.services.taxonomy_industry_map import (
    buyers_from_taxonomy_table,
    map_company_industries,
    write_taxonomy_industries,
)
from app.services.taxonomy_live_match import compose_taxonomy_job_search

ROOT = Path(__file__).resolve().parents[1]

PREVIEWS = (
    {
        "label": "Gritt",
        "url": "https://gritt.ai",
        "snapshot": ROOT / "tests/fixtures/robot_pages/con-01/page.txt",
    },
    {
        "label": "Richtech Robotics",
        "url": "https://richtechrobotics.com",
        "snapshot": ROOT / "tests/fixtures/robot_pages/hos-03/page.txt",
        "product": "ADAM",
    },
    {
        "label": "Miso Robotics",
        "url": "https://misorobotics.com",
        "snapshot": ROOT / "tests/fixtures/robot_pages/food-01/page.txt",
    },
    {
        "label": "Avidbots",
        "url": "https://avidbots.com",
        "snapshot": ROOT / "tests/fixtures/robot_pages/cln-01/page.txt",
    },
    {
        "label": "Locus Robotics",
        "url": "https://locusrobotics.com",
        "snapshot": ROOT / "tests/fixtures/robot_pages/log-01/page.txt",
    },
)


def load_companies(path: Path) -> list[dict]:
    companies = []
    with path.open(newline="", encoding="utf-8") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            readiness, source_kind = readiness_from_signals(row.get("stage"), row.get("why"))
            companies.append(
                {
                    "id": index,
                    "name": (row.get("company") or "").strip(),
                    "industry": (row.get("industry") or "").strip(),
                    "readiness": readiness,
                    "source_kind": source_kind,
                    "functions": [],
                }
            )
    return companies


def seed_map(companies: list[dict], db_path: Path) -> dict:
    planned = map_company_industries(companies)
    engine = create_engine(f"sqlite:///{db_path}")
    Company.__table__.create(engine)
    CompanyTaxonomyIndustry.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    by_id = {row["id"]: row for row in companies}
    for row in planned["mapped"]:
        source = by_id[row["company_id"]]
        session.add(
            Company(
                id=source["id"],
                name=source["name"] or "unknown",
                industry=source["industry"] or None,
            )
        )
    session.flush()
    written = write_taxonomy_industries(session, planned["mapped"])
    session.commit()
    buyers = buyers_from_taxonomy_table(session)
    session.close()
    return {
        "written": written,
        "buyers": buyers,
        "unmapped": planned["unmapped"],
        "mapped_count": len(planned["mapped"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buyers", default=str(ROOT / "reports/buyer_readiness.csv"))
    parser.add_argument("--output", default=str(ROOT / "reports/taxonomy_preview_five.json"))
    parser.add_argument("--sqlite", default=str(ROOT / "reports/taxonomy_preview.sqlite"))
    args = parser.parse_args()

    buyers_path = Path(args.buyers)
    sqlite_path = Path(args.sqlite)
    if sqlite_path.exists():
        sqlite_path.unlink()
    seeded = seed_map(load_companies(buyers_path), sqlite_path)
    unmapped_labels = Counter(
        row["industry_text"] or "(blank)" for row in seeded["unmapped"]
    )
    people_postings = sum(1 for row in seeded["buyers"] if row.get("source_kind") == "job_board")
    results = []
    for item in PREVIEWS:
        page_text = item["snapshot"].read_text(encoding="utf-8", errors="replace")
        composed = compose_taxonomy_job_search(
            item["url"],
            product=item.get("product"),
            page_text=page_text,
            buyers=seeded["buyers"],
            unmapped=seeded["unmapped"],
        )
        results.append(
            {
                "label": item["label"],
                "url": item["url"],
                "product_hint": item.get("product"),
                "page_words": len(page_text.split()),
                "state": composed["state"],
                "company_name": composed.get("company_name"),
                "robot_name": composed.get("robot_name"),
                "products": composed.get("taxonomy_products") or [],
                "job_count": composed.get("job_count"),
                "jobs": [
                    {
                        "company_name": job.get("company_name"),
                        "industry": job.get("industry"),
                        "readiness": job.get("readiness"),
                        "function_matched": job.get("function_matched"),
                        "title": job.get("title"),
                        "why": job.get("why"),
                        "source": job.get("source"),
                    }
                    for job in (composed.get("jobs") or [])[:8]
                ],
            }
        )
        print(
            f"{item['label']}: {composed.get('robot_name')} "
            f"products={len(composed.get('taxonomy_products') or [])} "
            f"buyers={composed.get('job_count')}"
        )

    payload = {
        "environment": "local preview, production database not opened",
        "flag": "TAXONOMY_MATCH_ENABLED default off; this script calls the composer directly",
        "sqlite": str(sqlite_path),
        "mapped_rows": seeded["written"],
        "unmapped_count": len(seeded["unmapped"]),
        "unmapped_labels": unmapped_labels.most_common(),
        "people_posting_rows_stored_then_excluded": people_postings,
        "function_tags": "none on these company rows; matches are industry plus readiness",
        "results": results,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

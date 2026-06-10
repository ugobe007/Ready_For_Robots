#!/usr/bin/env python3
"""Humanoid benchmark secondary pass — five-pillar gap rescue + cited news evidence."""
from __future__ import annotations

import argparse
import json
import sys

from app.database import SessionLocal
from app.services.humanoid_secondary_pass import (
    run_humanoid_secondary_pass_batch,
    select_humanoid_repair_candidates,
)
from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps


def main() -> int:
    parser = argparse.ArgumentParser(description="Humanoid secondary pass (5 pillars)")
    parser.add_argument("--limit", type=int, default=15, help="Max robots to repair")
    parser.add_argument("--sparse-pct", type=float, default=85.0, help="Sparse spec threshold")
    parser.add_argument("--audit-only", action="store_true", help="Gap audit only, no rescue")
    parser.add_argument("--no-llm", action="store_true", help="Skip per-robot news/LLM scrape")
    parser.add_argument("--no-news", action="store_true", help="Skip fleet deployment news scan")
    parser.add_argument("--news-queries", type=int, default=20, help="Cap RSS queries for news scan")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.audit_only:
            summary = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=args.sparse_pct)
            candidates = select_humanoid_repair_candidates(
                db, limit=args.limit, sparse_threshold_pct=args.sparse_pct
            )
            out = {
                "avg_spec_fill_pct": summary.get("avg_spec_fill_pct"),
                "robots_sparse_specs": summary.get("robots_sparse_specs"),
                "catalog_not_in_db_count": summary.get("catalog_not_in_db_count"),
                "field_coverage_bottom_10": (summary.get("field_coverage") or [])[:10],
                "repair_candidates": candidates,
            }
            print(json.dumps(out, indent=2, default=str))
            return 0

        stats = run_humanoid_secondary_pass_batch(
            db,
            limit=args.limit,
            sparse_threshold_pct=args.sparse_pct,
            use_llm_scrape=not args.no_llm,
            persist_deployment_news=not args.no_news,
            deployment_query_cap=args.news_queries,
        )
        print(json.dumps(stats, indent=2, default=str))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

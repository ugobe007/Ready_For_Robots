#!/usr/bin/env python3
"""Humanoid gap logic engine — what's missing, find it, rescore HEIF."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import SessionLocal
from app.services.humanoid_gap_engine import (
    build_humanoid_data_plan,
    run_humanoid_gap_engine_batch,
    run_humanoid_gap_engine_for_slug,
)
from app.services.humanoid_secondary_pass import select_humanoid_repair_candidates
from app.services.humanoid_spec_gaps import analyze_humanoid_spec_gaps


def main() -> int:
    parser = argparse.ArgumentParser(description="Humanoid gap engine second pass")
    parser.add_argument("--limit", type=int, default=15, help="Max robots to repair")
    parser.add_argument("--sparse-pct", type=float, default=85.0, help="Sparse spec threshold")
    parser.add_argument("--slug", type=str, default=None, help="Single model_slug")
    parser.add_argument("--audit-only", action="store_true", help="Fleet gap audit only")
    parser.add_argument("--plan-only", action="store_true", help="Build data plans only, no scrape")
    parser.add_argument("--no-llm", action="store_true", help="Skip per-robot news/LLM scrape")
    parser.add_argument("--no-news", action="store_true", help="Skip fleet deployment news scan")
    parser.add_argument("--news-queries", type=int, default=20, help="Cap RSS queries for news scan")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.slug:
            out = run_humanoid_gap_engine_for_slug(
                db,
                args.slug,
                use_llm_scrape=not args.no_llm,
                plan_only=args.plan_only,
            )
            print(json.dumps(out, indent=2, default=str))
            return 0

        if args.audit_only or args.plan_only:
            summary = analyze_humanoid_spec_gaps(db, sparse_threshold_pct=args.sparse_pct)
            candidates = select_humanoid_repair_candidates(
                db, limit=args.limit, sparse_threshold_pct=args.sparse_pct,
            )
            out = {
                "avg_spec_fill_pct": summary.get("avg_spec_fill_pct"),
                "robots_sparse_specs": summary.get("robots_sparse_specs"),
                "catalog_not_in_db_count": summary.get("catalog_not_in_db_count"),
                "field_coverage_bottom_10": (summary.get("field_coverage") or [])[:10],
                "repair_candidates": candidates,
            }
            if args.plan_only:
                plans = []
                for cand in candidates:
                    row = db.execute(
                        text("""
                            SELECT model_slug, name, vendor, status, product_url, specs, sources,
                                   heif_total, score_total, last_scraped_at
                            FROM humanoid_benchmarks WHERE model_slug = :slug
                        """),
                        {"slug": cand["model_slug"]},
                    ).mappings().first()
                    if row:
                        plans.append(build_humanoid_data_plan(dict(row)))
                out["data_plans"] = plans
            print(json.dumps(out, indent=2, default=str))
            return 0

        stats = run_humanoid_gap_engine_batch(
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

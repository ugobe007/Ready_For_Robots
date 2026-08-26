#!/usr/bin/env python3
"""Ingest the operator OEM/SKU workbook into the ontology + FIND vendor index.

  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py
  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --lookup-urls
  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --apply

`--lookup-urls` fetches candidate pages with the Understanding fetcher
(rate-limited). Only verified URLs are stored. Stretch-on-Spot is skipped.

`--apply` upserts manufacturers + robot_models (FIND catalog tables).
Requires DATABASE_URL or HARNESS_DATABASE_URL. Does not invent credentials.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.oem_sku_catalog import (  # noqa: E402
    LOOKUP_PATH,
    ONTOLOGY_PATH,
    SEED_PATH,
    XLSX_PATH,
    apply_to_catalog,
    apply_verified_urls,
    compile_vendor_seed,
    lookup_urls,
    parse_workbook,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", default=str(XLSX_PATH))
    parser.add_argument("--lookup-urls", action="store_true", help="Fetch/verify product URLs")
    parser.add_argument("--rate-limit", type=float, default=0.5)
    parser.add_argument("--max-fetches", type=int, default=None)
    parser.add_argument("--apply", action="store_true", help="Upsert manufacturers + robot_models")
    args = parser.parse_args()

    catalog = parse_workbook(Path(args.xlsx))
    lookup = None
    if LOOKUP_PATH.is_file() and not args.lookup_urls:
        try:
            lookup = json.loads(LOOKUP_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            lookup = None
    if args.lookup_urls:
        lookup = lookup_urls(
            catalog,
            rate_limit_s=args.rate_limit,
            max_fetches=args.max_fetches,
        )
        write_json(LOOKUP_PATH, lookup)
        print(
            "URL lookup",
            lookup.get("counts"),
            f"wrote {LOOKUP_PATH.relative_to(ROOT)}",
        )
    if lookup:
        apply_verified_urls(catalog, lookup)
    write_json(ONTOLOGY_PATH, catalog)
    seed = compile_vendor_seed(catalog)
    write_json(SEED_PATH, seed)
    print(
        f"wrote {ONTOLOGY_PATH.relative_to(ROOT)} companies={catalog['company_count']} "
        f"products={catalog['product_count']}"
    )
    print(
        f"wrote {SEED_PATH.relative_to(ROOT)} vendors={seed['vendor_count']} "
        f"robots={seed['robot_count']}"
    )
    verified_urls = sum(1 for v in seed["vendors"] for r in v["robots"] if r.get("product_url"))
    print(f"verified product_url rows={verified_urls}")

    if args.apply:
        from scripts.harness_env import load_harness_env

        meta = load_harness_env(ROOT)
        if meta.get("status") != "configured":
            print(
                "DATABASE_URL not configured — skip apply. "
                "Leftover: PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --apply",
                file=sys.stderr,
            )
            return 2
        stats = apply_to_catalog(seed)
        print("DB apply", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

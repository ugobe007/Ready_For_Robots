#!/usr/bin/env python3
"""Ingest the operator OEM/SKU workbook into the ontology + FIND vendor index.

  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py
  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --lookup-urls
  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --discover-skus
  PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --apply

`--lookup-urls` fetches candidate pages with the Understanding fetcher
(rate-limited). Only verified URLs are stored. Stretch-on-Spot is skipped.

`--discover-skus` walks official product listing pages on verified OEM hosts
and indexes additional named SKUs. Resume-friendly. Does not invent SKUs.

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
    DISCOVERY_PATH,
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
from app.services.oem_sku_discover import (  # noqa: E402
    discover_skus,
    merge_discovered_skus,
    merge_lookup_rows,
    scrub_discovery,
)


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", default=str(XLSX_PATH))
    parser.add_argument("--lookup-urls", action="store_true", help="Fetch/verify product URLs")
    parser.add_argument(
        "--discover-skus",
        action="store_true",
        help="Discover named SKUs from official OEM listing pages",
    )
    parser.add_argument("--oem", default=None, help="Limit discovery to one company slug")
    parser.add_argument("--rate-limit", type=float, default=0.45)
    parser.add_argument("--max-fetches", type=int, default=None)
    parser.add_argument("--max-new-per-oem", type=int, default=16)
    parser.add_argument("--apply", action="store_true", help="Upsert manufacturers + robot_models")
    args = parser.parse_args()

    catalog = parse_workbook(Path(args.xlsx))
    lookup = _load_json(LOOKUP_PATH)
    if args.lookup_urls:
        lookup = lookup_urls(
            catalog,
            rate_limit_s=args.rate_limit,
            max_fetches=args.max_fetches,
            prior=lookup,
        )
        write_json(LOOKUP_PATH, lookup)
        print(
            "URL lookup",
            lookup.get("counts"),
            f"wrote {LOOKUP_PATH.relative_to(ROOT)}",
        )
    discovery = _load_json(DISCOVERY_PATH)
    if discovery:
        discovery = scrub_discovery(discovery)
        write_json(DISCOVERY_PATH, discovery)
    if args.discover_skus:
        discovery = discover_skus(
            catalog,
            rate_limit_s=args.rate_limit,
            max_fetches=args.max_fetches,
            max_new_per_oem=args.max_new_per_oem,
            oem_slug=args.oem,
            prior=discovery,
        )
        write_json(DISCOVERY_PATH, discovery)
        print(
            "SKU discovery",
            discovery.get("counts"),
            f"wrote {DISCOVERY_PATH.relative_to(ROOT)}",
        )
        lookup = merge_lookup_rows(lookup, discovery)
        write_json(LOOKUP_PATH, lookup)
    if discovery:
        merge_discovered_skus(catalog, discovery)
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

# Outcome — Vendor robots URL lookup backfill

**Mission:** `missions/2026-08-21-vendor-robots-url-lookup`  
**Type:** build  
**Date:** 2026-08-21

## What shipped

Jobs URL submit now looks up the manufacturer host against `app/data/vendor_robots_index.json` (scraped from https://readyforrobots.com/robots / `GET /api/humanoid/robots`) and returns that vendor's stored SKUs plus a lightweight specs profile. Homepage crawl may add extra SKUs; it does not replace the index. Press hosts are never lookup keys.

Rebuild:

```bash
PYTHONPATH=. python3 scripts/backfill_vendor_robots_from_index.py
PYTHONPATH=. python3 scripts/backfill_vendor_robots_from_index.py --apply   # manufacturers + robot_models when DATABASE_URL is set
```

Industrial / commercial lists later append the same JSON shape (`list_category`).

## Index

| Metric | Result |
|--------|--------|
| Source | `https://ready-2-robot.fly.dev/api/humanoid/robots` |
| Vendors | 74 |
| Robots | 129 (full /robots list) |
| Skipped (no OEM domain) | 0 |

Examples: `unitree.com` → G1 / H1 / R1 / H2 Plus; `engineai.com` + `engineai.com.cn` → PM01 / SA01 / T800; `ubtrobot.com` → Walkers + U1s; `agibot.com` → A2 / G5 / A3 / G2 / X2. Homepage does not auto-select a SKU (`/g1` selects G1). Morningstar / TMCnet miss.

## Tests

`pytest tests/test_vendor_robot_lookup.py tests/test_product_href_discovery.py tests/test_robot_job_search.py` → 29 passed.

## Follow-ups

- `--apply` against production `DATABASE_URL` (not available in this cloud env).
- Fly deploy so Jobs API serves the JSON.
- Industrial / commercial ontology lists using the same index shape.
- Richtech is not on `/robots`; archive/prose identity remains a separate path.

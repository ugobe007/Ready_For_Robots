# Outcome: Pipeline cache refresh health

**Date:** 2026-06-23  
**Status:** done

## Cache rebuild

Ran `python3 scripts/refresh_pipeline_cache.py` against production DB (~69s):

| Surface | Count |
|---------|-------|
| `pipeline_feed_leads` | **35** (durable cache) |
| `homepage_hot_leads` | 46 |
| `leads_50_all` | 50 |
| `leads_12_HOT` | 12 |
| `humanoid_robots` | 109 |

## Live API (after rebuild)

| Metric | Value |
|--------|-------|
| `built_at` | `2026-06-22T20:37:01Z` |
| `cache_pending` | `null` |
| Anonymous `leads_count` | **9** (entitlement-trimmed; healthy) |
| `visible_count` | 9 |

Sample leads: Accor Hotels, MGM Resorts, Norwegian Cruise Line — industries populated post rescue sweep.

## Harness fix

`snapshot.pipeline_surface.tiers` now reads `priority_tier` from pipeline payloads (was always `unknown`).

## Deploy

Not required — cache lives in `pipeline_cache_store` (Postgres); Fly serves updated feed immediately.

## Next

Rank 2: `pipeline-action-copy` — industry-specific SIGNAL blurbs now unblocked.

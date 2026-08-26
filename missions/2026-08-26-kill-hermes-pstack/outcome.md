# Outcome — Kill Hermes; use pstack in the IDE

**Status:** in progress  
**Branch:** `cursor/kill-hermes-pstack-009b`

## What shipped

- Hermes retired in constitution, product docs, and verify-readyforrobots.
- Ingest family returns 410 unless `HERMES_INGEST_ENABLED=1`.
- Hermes scripts refuse unless `HERMES_RETIRED_OVERRIDE=1`.
- `hermes-fly-smoke.yml` is skip-by-default and never `--apply`s.
- `fly.toml`: `CAL_AUTONOMY_ENABLED` 1 → 0; `ENABLE_SCHEDULED_CAL_AUTONOMY` 1 → 0.
- Checked-in pstack rules (IDE only). Matcher and ontology untouched.

## Cal flag

| Flag | Before | After |
|------|--------|-------|
| `CAL_AUTONOMY_ENABLED` | `1` | `0` |
| `ENABLE_SCHEDULED_CAL_AUTONOMY` | `1` | `0` |

`[env]` in `fly.toml` needs a Fly deploy to land. Not set: `HERMES_INGEST_ENABLED`, `MARKET_GRAPH_RUN_RESEARCH`, `LEAD_RESEARCH_AGENT_ENABLED`.

## Tests

Pending in this file until pytest runs.

# Mission: Daily orchestrator cycle

**Date:** {date}
**Agent:** Orchestrator
**Status:** in_progress
**Type:** build

## Goal

Run one highest-impact improvement from the latest harness snapshot and `docs/market_thesis.md` backlog.

## Acceptance criteria

- [ ] `python3 scripts/harness_snapshot.py` run; before/after metrics recorded in `outcome.md`
- [ ] If `cache_pending` is true or `built_at` is missing/stale (>26h), run `python3 scripts/refresh_pipeline_cache.py --remote --wait`
- [ ] Execute **one** build mission aligned with north star (**names/events first**)
- [ ] Run verification gates from `harness/gates.yaml` where applicable
- [ ] Autonomous mode: commit, push, and deploy when the mission requires it
- [ ] Write `outcome.md` with metrics delta and follow-ups
- [ ] Run `python3 scripts/harness_notify.py --mission missions/{mission_slug}`

## Context

Autonomous **daily harness cycle**. Read snapshot `intelligence` (junk_rate, gap_frequency, industry_top) and the ranked backlog in `docs/market_thesis.md`.

If the backlog has no open ranks, pick the top friction theme from the snapshot (vendor/OEM leak, contact gaps, cache health, conversion funnel).

Standing ProductSurface directive: see `docs/conversion_agent_challenges.md`.

## Out of scope

- Force push to `main`
- Committing `reports/` artifacts
- Parallel local + Fly pipeline cache refresh
- Committing `.env` files

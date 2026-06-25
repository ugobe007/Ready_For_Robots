# Mission: Daily orchestrator cycle

**Date:** {date}
**Agent:** Orchestrator
**Status:** in_progress
**Type:** build

## Goal

Run one highest-impact improvement that advances **PMF**: automated sales pipeline for robot companies (signup → funnel automation → native CRM or HubSpot). Use the latest harness snapshot and `docs/market_thesis.md` backlog.

## Acceptance criteria

- [ ] `python3 scripts/harness_snapshot.py` run; before/after metrics recorded in `outcome.md`
- [ ] If `cache_pending` is true or `built_at` is missing/stale (>26h), run `python3 scripts/refresh_pipeline_cache.py --remote --wait`
- [ ] Execute **one** build mission aligned with `docs/product_market_fit.md` (conversion/activation first unless snapshot shows P0 junk blocking pipeline trust)
- [ ] Run verification gates from `harness/gates.yaml` where applicable
- [ ] Autonomous mode: commit, push, and deploy when the mission requires it
- [ ] Write `outcome.md` with metrics delta and follow-ups
- [ ] Run `python3 scripts/harness_notify.py --mission missions/{mission_slug}`

## Context

Autonomous **daily harness cycle**. Read `docs/product_market_fit.md` first, then snapshot `intelligence` (junk_rate, gap_frequency, industry_top) and the ranked backlog in `docs/market_thesis.md`.

**Mission selection priority:**
1. Conversion / activation (signup, first save, CRM or HubSpot connect, pipeline motion)
2. Pipeline trust blockers (empty feed, vendor/OEM leak in live slice, cache health)
3. Lead quality only when junk prevents reps from trusting the funnel

Standing ProductSurface directive: see `docs/conversion_agent_challenges.md`.

## Out of scope

- Force push to `main`
- Committing `reports/` artifacts
- Parallel local + Fly pipeline cache refresh
- Committing `.env` files

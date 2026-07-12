# Mission: Daily orchestrator cycle

**Date:** 2026-07-12
**Agent:** Orchestrator
**Status:** in_progress
**Type:** build

## Goal

Run one highest-impact improvement that advances **signups and PMF**: robot OEM reps must sign up, see value on `/pipeline`, and save their first lead. Use the latest harness snapshot and `docs/market_thesis.md` backlog.

**Operator directive:** Ship today. Autonomous code changes, commits, pushes, and deploys are **pre-approved** when gates pass. Signups beat everything else.

## Acceptance criteria

- [ ] `python3 scripts/harness_snapshot.py` run; diagnostics + before/after metrics in `outcome.md`
- [ ] Review `reports/harness_daily_report_latest.md` — site health, code review, conversion section
- [ ] If `cache_pending` is true or `built_at` is missing/stale (>26h), run `python3 scripts/refresh_pipeline_cache.py --remote --wait`
- [ ] Execute **one** build mission that improves **signup conversion or revenue** (UI, UX, copy, checkout, or workflow) — see `docs/conversion_agent_challenges.md`
- [ ] Run verification gates from `harness/gates.yaml` (including `site_health_smoke` and `code_conventions`)
- [ ] **Autonomous mode:** commit, push, and deploy — do not wait for human approval
- [ ] Write `outcome.md` with metrics delta and follow-ups
- [ ] Run `python3 scripts/harness_notify.py --mission missions/2026-07-12-daily-cycle` (email must send)

## Context

Autonomous **daily harness cycle**. Read `docs/product_market_fit.md` first, then snapshot `intelligence` (junk_rate, gap_frequency, industry_top) and the ranked backlog in `docs/market_thesis.md`.

**Mission selection priority:**
1. **Signup / activation** — browse → signup → first save → pipeline motion (PRIMARY)
2. Demo & workflow — anonymous value proof, faster `/pipeline`, outreach preview
3. Pipeline trust blockers (empty feed, vendor/OEM leak) only when they block signup intent
4. Lead quality only when junk prevents reps from trusting the funnel

Standing ProductSurface directive: see `docs/conversion_agent_challenges.md`.

## Out of scope

- Force push to `main`
- Committing `reports/` artifacts
- Parallel local + Fly pipeline cache refresh
- Committing `.env` files

# Outcome — Submit Workflow Stabilization

**Date:** 2026-08-17  
**Mission:** [`brief.md`](./brief.md)

## Result

Jobs submit is one explicit transaction: **research privately, reveal once**. The public job tape keeps scrolling during research. Profile + jobs enter the UI together. Multi-product URLs stop at a picker before deep research. Grounded profiles are cached.

## State machine

`IDLE → RESEARCHING → PRODUCT_SELECTION? → COMPOSING_RESULTS → RESULTS`

No overlapping `isLoadingProfile` / `hasProfile` / `isMatching` / `jobs.length` conditions for the URL path. `data-submit-phase` is on the Jobs section.

## Server

- `POST /api/robot-job-search` returns the first-page model: `profile`, `job_count`, `top_jobs[5]`, `jobs`, `timings`.
- Timings: `resolve_ms`, `profile_ms`, `match_ms`, `total_ms`, `cached`.
- Profile cache: Redis when available, in-process fallback. TTL 6h (`ROBOT_PROFILE_CACHE_TTL_SEC`).
- Source fetch budget: `ROBOT_PROFILE_SOURCE_BUDGET_MS` default **12000** (not 5.5s). Do not starve source quality to hit a stopwatch. 8–10s uncached is acceptable if the UI stays stable. `0` disables the cap. Cache is what makes repeats 2–3s.

## UI

- Fixed two-column geometry (`0.38 / 0.62`). No panel resize on results.
- Research console uses completed stages, not a fake percent.
- Right tape fades slightly while researching; corpus does not swap until RESULTS.
- Boston Dynamics-style picker stays inside the left frame.

## Tests

`python3 -m pytest tests/test_robot_job_search.py tests/test_understanding_shadow.py -q`

## Follow-up

**Locked sequence (do not churn architecture):**

1. Deploy PR #13 (this) — Fly API + Vercel Jobs UI
2. Smoke six cases: Dexmate, Agility, Locus, Avidbots, Boston Dynamics, bad URL
3. Verify cached vs uncached timings (`timings.cached`, `total_ms`) — logged, not shown as percents
4. Deploy/check PR #12 ranking if not already live
5. Auth continuity
6. Telemetry
7. Final pre-traffic gate

Traffic / C04 stay **paused** until that gate passes.

**Live verify (no more UX before this):**

- Generic tape stays stable during research
- Left frame height does not jump across IDLE / RESEARCHING / PRODUCT_SELECTION / RESULTS
- Boston Dynamics picker runs before deep research; one profile request per selection
- Second cached submit is visibly faster and returns the same profile/job state
- Timings are in the payload / funnel events, not fake progress %
- Timeout or bad URL → deliberate recover/error, not a half-rendered results page

This environment cannot Fly-deploy (no `FLY_API_TOKEN`). Merge to `main` triggers `.github/workflows/deploy.yml`. Prefer `--skip-release-command` if Alembic times out (no migrations in this PR). `/api/robot-job-search` is **not** on Fly until that deploy.

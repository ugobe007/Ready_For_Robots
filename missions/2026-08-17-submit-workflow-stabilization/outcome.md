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
- Source fetch budget: `ROBOT_PROFILE_SOURCE_BUDGET_MS` (default 5500) so uncached research can match before every candidate page returns. Extractors unchanged.

## UI

- Fixed two-column geometry (`0.38 / 0.62`). No panel resize on results.
- Research console uses completed stages, not a fake percent.
- Right tape fades slightly while researching; corpus does not swap until RESULTS.
- Boston Dynamics-style picker stays inside the left frame.

## Tests

`python3 -m pytest tests/test_robot_job_search.py tests/test_understanding_shadow.py -q`

## Follow-up

- Deploy this before evaluating Digit ranking through the product.
- Auth continuity + telemetry remain next after MATCH TRUTH ranking ships.
- Live uncached/cached timings need a Fly deploy (`--skip-release-command`; no migrations).

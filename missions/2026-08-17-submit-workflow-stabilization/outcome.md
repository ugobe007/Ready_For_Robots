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

## Release checkpoint (do not add product work)

**Merge order:** #13 first, then six-case smoke, then #12. Do not merge ranking until submit workflow is proven, so a production issue can be attributed to workflow state or ranking — not both.

**#13 go-live bar:** PR merged → Fly `/api/robot-job-search` present → Vercel bundle current → six-case smoke PASS.

If #13 fails visually, fix only the submit transaction. If it passes, freeze it and move on.

**Contract check after deploy:** Vercel Jobs UI and Fly API must both speak `/api/robot-job-search`. A new frontend against a stale Fly route recreates half-state.

**Timing bar:** uncached 8–12s is a pass if the state is stable. Cached repeat must be materially faster **and** return the same product identity, profile tier/facts, and top jobs.

### Six-case smoke sheet

For each case record: uncached_ms, cached_ms, profile_request_count, search_request_count, state transitions, panel geometry moved? (Y/N), jobs flashed before reveal? (Y/N), final state. A 200 is not a pass.

| Case | Expected pass shape |
|------|---------------------|
| Dexmate | one stable research sequence → Vega + manipulation-heavy jobs |
| Agility | stable research → Digit + mixed manipulation/transport board |
| Locus | stable research → Origin + transport-only board |
| Avidbots | stable research → Neo + scrub-only board |
| Boston Dynamics | quick picker first → **one** selected-product deep research call → results |
| Bad URL | stable research → deliberate recover, **never** partial results |

Traffic / C04 stay **paused** until #13 smoke PASS, then #12, then auth continuity + telemetry, then the final pre-traffic gate.

This environment cannot merge or Fly-deploy (`gh` write and `FLY_API_TOKEN` unavailable). Merge #13 to `main` to run `.github/workflows/deploy.yml`. No migrations; `--skip-release-command` if Alembic times out. #12 remains open and must not ship first.

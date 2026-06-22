# Mission: Snapshot DB telemetry

**Date:** 2026-06-23
**Agent:** PipelineHealth
**Status:** done
**Type:** build

## Goal

Ensure `harness_snapshot.py` always loads a real Postgres URL and exposes DB connection status so the `intelligence` slice is trendable.

## Acceptance criteria

- [x] Shared `scripts/harness_env.py` loads `.env` + optional `HARNESS_DATABASE_URL`
- [x] Snapshot includes `database.telemetry` (`configured` | `connected` | `unavailable` + reason)
- [x] `run_mission.py` and `harness_notify.py` load harness env before running
- [x] Fresh snapshot shows `junk_reasons.available: true` and `gap_frequency.available: true`
- [x] Commit, push, notify

## Context

Friction baseline (2026-06-23) found `database: null` when agent ran snapshot without dotenv. Rank-1 backlog item.

## Out of scope

- Fly deploy (harness scripts only)
- Schema changes

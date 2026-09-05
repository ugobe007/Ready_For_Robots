# Hermes tracks 8–10 live smoke

**Date:** 2026-08-24  
**Type:** test  
**Agents:** PipelineHealth + Hermes

## Goal

Now that PR #113 is on Fly, prove buying-window, customer/vendor video ingest, and seed-targets accept authenticated `dry_run` against production. Do not persist synthetic overlays. Do not flip `CAL_INCLUDE_BUYING_WINDOW`.

## Acceptance

1. `scripts/hermes_auth_smoke.py` dry-runs tracks 8–10 (seed-targets GET + three POSTs with `dry_run: true`).
2. Unit test asserts those payloads stay `dry_run`.
3. GitHub Actions `hermes-fly-smoke.yml` still uses `--apply` for infer-qualify only.
4. Public pipeline buying-window / video overlay counts are allowed to stay 0 (Mac crons own real POSTs).

## Out of scope

Mac Hermes cron ticks. Cal buying-window ranking. Jobs UI.

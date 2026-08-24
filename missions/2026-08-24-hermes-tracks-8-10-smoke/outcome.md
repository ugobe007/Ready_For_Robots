# Outcome — Hermes tracks 8–10 live smoke

**Date:** 2026-08-24  
**Type:** test  
**Status:** code + unit tests; Fly proof via GHA `hermes-fly-smoke.yml`

## Code

`scripts/hermes_auth_smoke.py` now dry-runs, after infer-qualify:

- `GET /video-evidence/seed-targets?kind=both&missing_only=true&limit=5`
- `POST /buying-window-overlay` `dry_run: true`
- `POST /video-evidence/ingest` `dry_run: true`
- `POST /vendor-video-evidence/ingest` `dry_run: true`

`--apply` still persists **infer-qualify only**. Synthetic 8–10 bodies stay `dry_run`.

Local: `tests/test_hermes_auth_smoke.py` + ingest tests **18 passed**.

## Not this cycle

Mac crons POSTing real buying-window / video overlays. `CAL_INCLUDE_BUYING_WINDOW` stays off.

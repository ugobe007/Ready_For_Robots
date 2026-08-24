# Outcome — Hermes tracks 8–10 live smoke

**Date:** 2026-08-24  
**Type:** test  
**Status:** Fly smoke green (GHA `32687223021`)

## Fly (GHA `--apply` on this PR)

Run [32687223021](https://github.com/ugobe007/Ready_For_Robots/actions/runs/32687223021): `tracks_8_10.ok` true.

| Call | Result |
|------|--------|
| seed-targets | **200**, `count` 10, `auth: admin_key` |
| buying-window dry_run | **200**, accepted 1, company 79 |
| video ingest dry_run | **200**, accepted 1 |
| vendor-video dry_run | **200**, accepted 1 |

`--apply` infer-qualify still accepted 5. Synthetic 8–10 bodies were `dry_run` (not persisted).

## Code

`scripts/hermes_auth_smoke.py` now dry-runs, after infer-qualify:

- `GET /video-evidence/seed-targets?kind=both&missing_only=true&limit=5`
- `POST /buying-window-overlay` `dry_run: true`
- `POST /video-evidence/ingest` `dry_run: true`
- `POST /vendor-video-evidence/ingest` `dry_run: true`

`--apply` still persists **infer-qualify only**. Synthetic 8–10 bodies stay `dry_run`.

Local: `tests/test_hermes_auth_smoke.py` + ingest tests **18 passed**. GHA Fly smoke **success** (`32687223021`).

## Not this cycle

Mac crons POSTing real buying-window / video overlays. `CAL_INCLUDE_BUYING_WINDOW` stays off.

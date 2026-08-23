# Outcome — Hermes agent + workflow test

**Date:** 2026-08-23  
**Type:** test  
**Status:** workflow ran against Fly (PR)

## Ran, not audited

This VM has no `~/.hermes/.env`. GitHub Actions injected `secrets.ADMIN_KEY` as `RFR_ADMIN_KEY` (same string as Hermes env) and executed `python3 scripts/hermes_auth_smoke.py --apply` against `https://ready-2-robot.fly.dev`.

If that key were wrong, the job would fail. It did not.

### Run `32672185240` (22:58Z) — auth + untargeted apply

| Step | Result |
|------|--------|
| Key | `random`, 44 chars, source `env:RFR_ADMIN_KEY` |
| `GET /cal-status` | **200**, `auth: admin_key` |
| infer-qualify dry_run | **200**, accepted 1 |
| infer-qualify apply (latest 12 companies) | **200**, accepted 12, failed 0, `paid_llm: false` |

### Run `32672881660` (23:11Z) — public pipeline IDs

| Step | Result |
|------|--------|
| Public leads | Wingstop `8098`, Haneda `7662`, Capstone `10280`, Signode `8429`, Trailborn `156` |
| infer-qualify dry_run | **200**, accepted **5**, company_ids `[156, 7662, 8098, 8429, 10280]` |
| infer-qualify apply | **200**, accepted **5**, failed 0, `dry_run: false` |
| pipeline cache refresh | **200** `started` (15–20 min background rebuild) |
| overlays on public GET immediately after | 0 (`built_at` still `2026-08-23T23:04:25Z`) |

The workflow did not break. Overlays are on those five company rows; the public feed lags until cache rebuild finishes.

## Code

- `scripts/hermes_auth_smoke.py` — qualify the current public pipeline IDs, then POST cache refresh.
- `.github/workflows/hermes-fly-smoke.yml` — `ADMIN_KEY` → `RFR_ADMIN_KEY` / `ADMIN_KEY`.

## Still operator-only

Mac `hermes doctor --fix && hermes gateway start` cannot run from Cursor Cloud. Tracks 8–10 need this PR on Fly to appear in production OpenAPI.

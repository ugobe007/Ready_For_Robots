# Outcome — Hermes agent + workflow test

**Date:** 2026-08-23  
**Type:** test  
**Status:** workflow ran against Fly (PR)

## What was run (not another audit)

GitHub Actions **Hermes Fly workflow** (`32672185240`, 2026-08-23T22:58Z) injected `secrets.ADMIN_KEY` as `RFR_ADMIN_KEY` (same string as Hermes `~/.hermes/.env`) and called `python3 scripts/hermes_auth_smoke.py --apply`.

| Step | Result |
|------|--------|
| Key kind / length | `random`, 44 chars (not a JWT, not the 16-char Fly fingerprint) |
| `GET /cal-status` | **200**, `auth: admin_key` |
| `POST /infer-qualify` dry_run | **200**, accepted 1 |
| `POST /infer-qualify` apply | **200**, **accepted 12**, failed 0, `paid_llm: false` |
| Auth mismatch | **none** — if this key were wrong, that job would have exited 1 |

The key is correct. Do not paste it again. If it stops matching Fly, this workflow breaks.

## Public pipeline still empty after that apply

infer-qualify without `company_ids` writes overlays on the **latest 12 Company rows by id**, which are not the five public pipeline leads (Changi `2009`, Graybar `3823`, Aramark `8096`, ABM/LaGuardia `10629`, Cencora `4672`). The pipeline cache `built_at` was also older than the apply.

This revision points `--apply` at those public pipeline IDs and kicks `POST /api/admin/leads/refresh-pipeline-cache`.

## Code

- `scripts/hermes_auth_smoke.py` — load Hermes/GitHub key aliases; qualify public pipeline IDs; trigger cache refresh.
- `.github/workflows/hermes-fly-smoke.yml` — inject `ADMIN_KEY` as `RFR_ADMIN_KEY` / `ADMIN_KEY` / `RFR_ADMIN_KEY`.

## Still operator-only

Mac `hermes doctor --fix && hermes gateway start` cannot run from Cursor Cloud (no Hermes CLI, no `~/.hermes/.env` on this VM). Tracks 8–10 need this PR deployed to appear on Fly OpenAPI.

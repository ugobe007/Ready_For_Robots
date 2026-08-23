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

Public GET after cache rebuild (`built_at` **2026-08-23T23:18:08Z**): **5/5** leads have `hermes_qualify` (Accor 98, Stellantis 88, MGM 99, Dubai Airports 67, Zoox 54). The workflow wrote overlays; the feed caught up.

## Hermes doctor (Mac) — 3 findings, gateway still started

`hermes doctor --fix` then gateway start reported:

| # | Doctor line | What it is | Action |
|---|-------------|------------|--------|
| 1 | `web` workspace 1 npm vulnerability | Hermes Agent install (`NousResearch/hermes-agent` `web/`), **devDependency** graph. `npm audit --omit=dev` is clean. Open upstream: [#68736](https://github.com/NousResearch/hermes-agent/issues/68736). | Not ReadyForRobots. Do not `npm audit fix` this repo. |
| 2 | `ui-tui` workspace 2 npm vulnerabilities | Same upstream TUI workspace, same class of build-tool advisories. | Same. |
| 3 | `Run 'hermes setup' to configure missing API keys` | Nous Portal / LLM / tool-gateway keys in `~/.hermes/.env`. **Not** `RFR_ADMIN_KEY`. | On the Mac only: `hermes setup --portal`. Skip if ingest-only; Fly already accepts the Hermes `RFR_ADMIN_KEY`. |

`✓ Service started` means the gateway is up. RFR ingest does not need item 3.

## Code

- `scripts/hermes_auth_smoke.py` — qualify the current public pipeline IDs, then POST cache refresh.
- `.github/workflows/hermes-fly-smoke.yml` — `ADMIN_KEY` → `RFR_ADMIN_KEY` / `ADMIN_KEY`.

## Still operator-only

`hermes setup --portal` is interactive on the Mac. Tracks 8–10 need this PR on Fly to appear in production OpenAPI.

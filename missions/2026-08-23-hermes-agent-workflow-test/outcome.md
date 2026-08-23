# Outcome — Hermes agent + workflow test

**Date:** 2026-08-23  
**Type:** test  
**Status:** tested (PR)

## What was tested

| Layer | Result |
|-------|--------|
| Unit ingest (job / qualify / contacts / vendor news / infer-qualify auth / digest auth) | pass |
| Dry-run qualify + contacts without a `companies` table | **was failing** — dry_run still queried SQLite. Fixed. |
| New tracks 8–10 dry_run + OpenAPI contract | pass locally |
| Live Fly ingest auth | unauth **403**, fingerprint **401**, JWT **401** |
| Live reconstruct | **200** `work:unknown:b8f7c8bb698e` |
| Live pipeline overlays | 5 leads, **0** Hermes overlays |
| Live vendor news / deployment evidence | present (OTTO, Geek+, Locus; Agility/Schaeffler, Figure/BMW) |
| GHA Cal daily digest (15:12 UTC today) | **403** — ran *before* PR #111 body-print; GitHub `ADMIN_KEY` still rejected |
| Mac Hermes CLI / gateway | not in this environment |

## Production probe

`python3 scripts/hermes_health_probe.py` (exit 1, expected until overlays + Fly deploy):

- Pipeline built `2026-08-23T22:34:25Z`, 5 leads, all `hermes_*` empty (Changi, Graybar, Aramark, ABM/LaGuardia, Cencora).
- Market-graph snapshot `completed` at `2026-08-23T17:35:58Z`. Scheduler not running.
- Ingest contract ok.
- Fly OpenAPI **missing** buying-window + video tracks until this PR is deployed.

## Diff

- `apply_qualify_overlay` / `ingest_contact` skip DB on `dry_run=true` (Hermes smoke must not require company rows).
- Implement documented ingest: `POST /buying-window-overlay`, `POST /video-evidence/ingest`, `POST /vendor-video-evidence/ingest`, `GET /video-evidence/seed-targets`.
- Expand `scripts/hermes_health_probe.py` with ingest auth + OpenAPI route check.

## Follow-ups (operator)

1. **[H/L]** Paste Hermes `RFR_ADMIN_KEY` → Fly `ADMIN_KEY` and GitHub Actions `ADMIN_KEY`. Then `hermes doctor --fix && hermes gateway start`.
2. **[H/M]** Deploy this PR to Fly so tracks 8–10 exist in production OpenAPI.
3. **[M/L]** After auth works, POST `/infer-qualify` once so pipeline overlays are non-empty.

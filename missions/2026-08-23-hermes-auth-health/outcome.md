# Outcome — Hermes health (auth + empty overlays)

**Date:** 2026-08-23  
**Type:** build  
**Status:** shipped (PR)

## Diagnosis

Hermes is not reaching Fly.

- Public pipeline: 5 leads, **0** Hermes overlays (`hermes_qualify` / jobs / DMs / windows / video).
- Floor manager log: still “Awaiting first cron tick” since 2026-08-14.
- GHA Cal daily digest: HTTP **403** on 2026-08-20/21/22 — GitHub `ADMIN_KEY` does not match Fly (often the 16-char `fly secrets list` fingerprint).
- Known leftover: Mac cron `--provider ai-gateway` HTTP 402 (2026-08-20).

Jobs FIND does not depend on Hermes. Cal/pipeline overlays do.

## Diff

- Ingest `_require_ingest_auth` rejects 16-char hex fingerprint with an explicit 401.
- GHA digest prints Fly error body.
- `scripts/hermes_health_probe.py` — public overlay coverage.
- `docs/agent_improvement_log.md` + bridge auth note.

## Verify

`pytest tests/test_hermes_intelligence_ingest.py::test_infer_qualify_rejects_fly_secrets_list_fingerprint` — passed.

`python3 scripts/hermes_health_probe.py` — exit 1, `any_overlay: 0`.

## Follow-ups (operator, Mac + GitHub secrets)

1. `hermes doctor --fix && hermes gateway start && hermes cron list` — no `ai-gateway`.
2. `ADMIN_KEY` is not a Supabase key. Push Hermes `RFR_ADMIN_KEY` onto Fly (`fly secrets set`); copy the same string to GitHub Actions. Do not use `SERVICE_ROLE_KEY`. `fly ssh printenv` cannot recover it.
3. POST `/api/v1/market-graph/infer-qualify` once overlays should appear.

# Outcome — Cal daily digest and worker match Jobs

**Date:** 2026-08-27  
**Branch:** `cursor/cal-jobs-digest-009b`  
**PR:** parent opens (ManagePullRequest not in this agent’s tool catalog). Push: `origin/cursor/cal-jobs-digest-009b`.

## What was leaking

| Leak | Cause | Fix |
|------|--------|-----|
| **Drafts: 16 with Autopilot OFF** | Digest counted any `CrmAccount` with an `outreach_draft` and a recent `updated_at` (pipeline/enrichment touches). `_draft_and_store` could still write from ingest/scout even when the scheduled autonomy thread was off. | When autopilot is off, `_draft_and_store` returns without writing. Digest reports scheduled drafts as `0 (paused)` and does not use `updated_at` as a draft cycle. |
| **Digest copy** | `build_industry_brief_payload` appended “1452 opportunity signals / sales teams should prioritize…”. Links were `/admin` `/inbox` `/calendar`. | Industry brief removed. Body leads with Jobs-path counts (matcher / kept / apply) and a Cal-frozen one-liner. Links: `/`, `/pipeline?src=jobs_activate`, `/admin`. |
| **Double-send (08-26 copies)** | Web (`SKIP_CELERY=1`) and worker both started the 15:00 UTC digest thread. Idempotency was get-then-set, so both could pass. | Worker owns the in-app thread. Web starts only if `CAL_DAILY_DIGEST_WEB_BACKUP=1`. Send claims the UTC day with Redis SET NX and releases on failure. GHA 15:05 remains backup. |
| **22 due follow-ups** | `process_due_enrollments` had no autonomy gate (Celery hourly + any manual/API call). Autonomy cycle also ran follow-ups when it ran. | `process_due_enrollments` returns `paused` when `CAL_AUTONOMY_ENABLED=0`. Scheduled cycle does not send follow-ups. HOT 300 stays leftover-queue copy, not a send list. |

Intros stay on the 0 path: `CAL_BUYER_SALES_ENABLED` default 0; scheduled cycle disabled; buyer-sales draft/send limits stay 0.

## Files

- `app/services/cal_autonomy.py` — scheduled draft gate; manual Run cycle flag; follow-ups held
- `app/services/sequence_runner.py` — due follow-ups held when autopilot off
- `app/services/cal_daily_digest.py` — Jobs copy, no industry brief, SET NX claim
- `app/services/scout_discovery_agent.py` — no Cal sales draft when paused
- `app/api/admin_extended.py` — `manual=True` on admin Run cycle
- `app/main.py` — digest thread worker-only
- `tests/test_cal_daily_digest.py`, `tests/test_cal_jobs_digest_gates.py`, `tests/test_cal_autonomy.py`
- `docs/hermes_retired.md`, `docs/skills/rfr-daily-email-digest.SKILL.md`
- `missions/2026-08-27-cal-jobs-digest/`

## Tests

```
/tmp/rfr-venv/bin/python -m pytest tests/test_cal_daily_digest.py tests/test_cal_jobs_digest_gates.py tests/test_cal_autonomy.py tests/test_cal_autonomy_toggle.py tests/test_cal_watchdog.py -q
# 45 passed
```

## Prod flags / deploy

`fly.toml` already has `CAL_AUTONOMY_ENABLED=0` and `ENABLE_SCHEDULED_CAL_AUTONOMY=0` from #148. **No flag deploy needed.** This branch is code: draft/follow-up gates, digest copy, double-send claim. Those land only after a normal app deploy. This mission did not `fly deploy` (no `fly.toml` flag change).

Do not set `MARKET_GRAPH_RUN_RESEARCH`, `HERMES_INGEST_ENABLED`, or `LEAD_RESEARCH_AGENT_ENABLED`.

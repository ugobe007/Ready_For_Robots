# Outcome — Kill Hermes; use pstack in the IDE

**Status:** done  
**Branch:** `cursor/kill-hermes-pstack-009b`  
**Commit:** `6378870f` plus follow-up

## What shipped

- Hermes retired in AGENTS.md, CLAUDE.md, product docs, and verify-readyforrobots.
- Ingest family returns **410** unless `HERMES_INGEST_ENABLED=1`.
- Hermes scripts refuse unless `HERMES_RETIRED_OVERRIDE=1`.
- `hermes-fly-smoke.yml` is skip-by-default and never `--apply`s.
- `fly.toml`: `CAL_AUTONOMY_ENABLED` 1 → 0; `ENABLE_SCHEDULED_CAL_AUTONOMY` 1 → 0.
- Checked-in pstack rules (IDE only). Matcher and ontology untouched.

## Cal flag

| Flag | Before | After |
|------|--------|-------|
| `CAL_AUTONOMY_ENABLED` | `1` | `0` |
| `ENABLE_SCHEDULED_CAL_AUTONOMY` | `1` | `0` |

`[env]` in `fly.toml` needs a Fly deploy to land. This VM has no `flyctl` / `FLY_API_TOKEN`, so production Cal is still on until deploy:

`fly deploy -a ready-2-robot --wait-timeout 600 --skip-release-command`

Not set: `HERMES_INGEST_ENABLED`, `MARKET_GRAPH_RUN_RESEARCH`, `LEAD_RESEARCH_AGENT_ENABLED`.

## Ingest gate

`_require_hermes_ingest` in `app/api/v1/market_graph.py`. Default 410: `Hermes ingest retired. Jobs uses POST /api/robot-job-match.`

Daily digest and cal-status stay on admin auth only.

## pstack

`.cursor/rules/pstack-jobs.mdc`  
`.cursor/rules/pstack-rfr.mdc`  
`docs/pstack_jobs.md`

## Tests

```
30 passed  tests/test_hermes_retired.py
            tests/test_hermes_intelligence_ingest.py
            tests/test_deployment_evidence_ingest.py
            tests/test_hermes_auth_smoke.py
            tests/test_robot_job_capability_match.py
```

Production matcher (no deploy this cycle): `POST /api/robot-job-match` HTTP 200, `state=matches`, 23 jobs.

Current Fly ingest (pre-deploy) still 403 without admin key. 410 lands after deploy.

## Follow-ups

1. Deploy this branch so Cal turns off and ingest returns 410.
2. Parent opens draft PR (ManagePullRequest missing in this run).
3. Do not merge until verify is green.

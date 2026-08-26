# Outcome — Integrate pstack into the Jobs site

**Status:** done  
**Branch:** `cursor/pstack-site-009b`  
**Commits:** `4828e8be` protocol + chrome; `5bc2fe4e` docs

## What shipped

- Jobs chrome `JobsPstackProtocol` on `/`, About (`/intelligence#jobs-protocol`), and a compact strip on the CRM desk.
- Runtime protocol: `readyforrobots-new/client/src/lib/pstackSite.ts` and `app/services/pstack_protocol.py` (How / Act / Critic).
- CRM generate-plan tagged pstack Act. How-check: copilot is not the matcher. ScoutChat frozen. Customer pstack chat refused.
- Constitution + verify-readyforrobots: pstack is site protocol + IDE routing. Critic is pstack. FIND is `/`. Hermes stays retired.

## Tests

```
37 passed  readyforrobots-new vitest
           client/src/lib/pstackSite.test.ts
           client/src/lib/jobsWorkflow.test.ts
5 passed   tests/test_pstack_protocol.py
```

Production matcher (no Fly deploy): `POST /api/robot-job-match` HTTP 200, `state=matches`, 16 jobs (chip `manipulates`). Named employers still present.

## Refused

- Vercel AI Gateway
- Hermes ingest
- Customer “chat with pstack”
- Replacing `robot_job_capability_match.py` with an LLM
- Removing the CRM signup wall
- Renaming process 03 CRM
- Fly deploy

## Follow-ups

1. Parent opens draft PR. ManagePullRequest is missing in this run. Compare: `https://github.com/ugobe007/Ready_For_Robots/pull/new/cursor/pstack-site-009b`
2. Do not merge until verify is green.
3. Frontend deploy on Vercel is what makes the chrome visible on readyforrobots.com.

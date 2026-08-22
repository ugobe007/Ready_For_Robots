# Outcome — Jobs CRM landing hides SIGNAL pipeline

**Date:** 2026-08-22  
**Mission:** `missions/2026-08-22-jobs-crm-no-pipeline`  
**Type:** build

## Diff

- `/crm?src=jobs_activate` (any Jobs handoff `src`) keeps CrmHero: 3 unlocked jobs, watch opt-in, `+ New robot`.
- Hides AdminNav, Back to pipeline, Cal queue, CrmPathFork, accounts table, and outreach editor.
- Signed-out Sign in uses `jobsSignupHref` with `next=/crm?src=…`, not bare `/login`.
- Skips `/api/crm/accounts` on the Jobs path. Header `/crm` without Jobs `src` still loads SIGNAL accounts/outreach.

## Metrics

Not a pipeline-cache mission. Jobs step 3 stays on the 3-job CRM, not SIGNAL chrome.

## Follow-ups

Paid CRM can show more than 3. Do not hop Jobs traffic onto pipeline buyers or Place outreach.

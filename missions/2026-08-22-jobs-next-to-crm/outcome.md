# Outcome — Next opens CRM; drop the Activate confirmation

**Date:** 2026-08-22  
**Mission:** `missions/2026-08-22-jobs-next-to-crm`  
**Type:** build

## Diff

- `jobsActivateHref` is `/crm?src=jobs_activate`. Signed-out Next goes to signup with that `next`.
- Snapshot carries **3** jobs (`CRM_UNLOCKED_JOBS`), matching the free CRM taste.
- `JobsHandoffBoard` redirects leftover `/pipeline?src=jobs_*` links. The “5 checked · 12 in this list / Save this job list to CRM” page is gone.
- CRM shows the 3 unlocked jobs from the handoff before opt-in.

## Metrics

Not a pipeline-cache mission. The extra activate page is no longer in the Jobs → CRM path.

## Follow-ups

Paid CRM can show more than 3. Do not bring the pipeline confirmation back.

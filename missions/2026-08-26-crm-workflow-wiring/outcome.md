# Outcome — Wire CRM into the Jobs workflow

**Date:** 2026-08-26  
**Status:** in PR

## Diff

- Process step 03 is **CRM**. Job-list CTA is **Open CRM →**.
- Checking a Keep row writes `rfr_jobs_handoff_v1` immediately (`jobsDumpedToCrm`).
- Open CRM / process 03 goes to `/pipeline?src=jobs_activate` with no signup wall.
- Jobs header shows CRM for anonymous users. Desk headline is CRM; **Place this job →** remains the money action inside the desk.

## Tests

`pnpm exec vitest run` jobsWorkflow / jobsQualify / jobsApply / jobsHandoffSnapshot — 47 passed.

## Follow-ups

Signed-in persistence of apply/follow-up. User may still refine CRM desk copy.

# Wire CRM into the Jobs workflow

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface

## Goal

CRM is step 03 of FIND → jobs → CRM. Checking a job dumps it into the CRM desk. **Open CRM** hits the **signup wall**, then the desk. Spec: `docs/jobs_crm.md`. Place this job stays the money action *inside* CRM. No SIGNAL, no robot OEMs.

## Acceptance

1. Process bar 03 is labeled **CRM**. Job-list CTA is **Open CRM →**.
2. Checking a Keep row writes the CRM handoff snapshot immediately.
3. Open CRM / process 03 uses `jobsCrmOpenHref`. Signed-out users go to `/signup?next=/pipeline?src=jobs_activate&src=jobs_activate`.
4. Jobs header shows CRM for anonymous users; click hits the wall. Bare `/crm` and `/pipeline` stay SIGNAL.
5. Signed-in CRM desk headline is CRM; Place this job remains the apply CTA. Pipeline activity is recorded on the job.
6. Canonical spec lives at `docs/jobs_crm.md`. Free entitlements constants: 5 / 15 per month / 7-day TTL (not enforced in API yet).

## Out of scope

Matcher retune. Account persistence of apply/follow-up. API expiry cron. Paid unlimited matching-job query. HubSpot/CSV export UI. Cal. Invented rental dollars.

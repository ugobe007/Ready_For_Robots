# Jobs CRM on pipeline: 5 jobs, Apply rectify, no SIGNAL OEMs

**Date:** 2026-08-25  
**Type:** build  
**Status:** shipped in PR (see git)

## Diff

- `jobsActivateHref` → `/pipeline?src=jobs_activate`. Header CRM and Next land on `JobsCrmDesk`.
- `CRM_UNLOCKED_JOBS = 5`. All five example jobs start Keep-checked.
- Pipeline Jobs `src` (including `jobs_automate`) renders the desk only — no SIGNAL leads, no Hermes OEM shortlist.
- `/crm?src=jobs_*` redirects to the same desk.
- Apply panel: pack / PoC / monthly rental (user-entered), outreach draft, workflow strategy, apply + follow-up tracking in sessionStorage.

## Metrics

N/A this cycle (UI contract). Do not invent rental dollars.

## Follow-ups

- Persist apply/follow-up on the account when signed in (today: sessionStorage).
- Watch opt-in still lives on SIGNAL `/crm` until the desk grows a watch row.

# Cal is the Jobs recruiter on CRM

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/cal-jobs-crm-copilot-009b` from `origin/main` plus CRM-first #202  
**Constraint:** Cal-as-core stays frozen. FIND stays `/`. Buyer mail stays off.

This is the review. `report.md` in this folder has the short version.

## What Cal can do now

After **Open CRM**, on `/pipeline?src=jobs_activate`, Cal works kept Job Cards.

He:

- Reads the kept list and the robot on this desk
- Asks the next missing apply fact, including task-model source vs we'll train it
- Stores that answer on `user_kept_jobs`
- Takes catalogued SKUs, the monthly price you type, and a skippable PoC
- Prepares the existing violet apply draft
- Leaves send to you

He does not invent emails, SKUs, employers, or model names.

## Where he lives

Signed Jobs CRM desk only. `CalJobsDesk` on `JobsCrmDesk`. Tools: `GET/POST /api/jobs-crm/cal/desk`.

FIND `/` has no Cal. pstack is still the merge gate, not a customer bot.

## What he still cannot do

- Hunt jobs on FIND
- Send buyer / SIGNAL mail
- Email the employer (you send)
- Run with `CAL_AUTONOMY_ENABLED` (production stays `0`)

## Included from #202

Open CRM is the only Jobs-for-robot list CTA. Task-model columns and `POST /api/jobs-crm/jobs/task-model` are on this branch. Not merged to main by this PR.

## Tests

Pytest: persona, tool routing, task-model persist, apply-draft prepare, refused FIND/buyer tools.  
Vitest: Cal on the desk, not on FIND, not Cal queue.  
`PYTHONPATH=/workspace python3 scripts/pstack_release.py --local` green, including `cal_jobs_desk`.

No Fly deploy. Draft only.

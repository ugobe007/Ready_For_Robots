# Outcome — CRM recruiter flow

**Branch:** `cursor/crm-recruiter-flow-009b`  
**Type:** build  
**PR:** parent opens (ManagePullRequest not in this agent tool catalog)

## Why Next steps was dead

Production JS (`index-C5QlG4Es.js`) already had `Next steps →` and `next=offer`, but the CRM desk control was a `<button type="button">` that only set React state. The offer form (`#jobs-next-steps`) mounted **below** the collected-job list, so a click looked like a dead link: no `href`, no `next=offer` query, no scroll. Off-desk FIND used `jobsCrmOfferHref`; the desk did not.

## What shipped

1. **Next steps / Apply** is `jobsCrmOfferHref` → `/pipeline?src=jobs_activate&next=offer#jobs-next-steps`. On the desk it opens and scrolls the offer form. Status bar **Apply →** is the same href after keep.
2. **One keep prompt:** `Keep these N jobs?` + **Yes**. N is selected count (3 stays 3). Dual Keep all 5 / Keep jobs removed. Yes persists selected cards, then Apply.
3. **Specs:** signed-in upload PDF/image (8 MB) to `user_robot_documents`. Selected docs attach via `application_documents` and the offer snapshot. Outreach gets token URLs; small files can ride as Resend attachments.
4. **Employer evaluate:** `/employer/:token` needs no RFR account. **Accept** and **Set up interview** (proposed time or “connect us”). Writes `application_messages` + status. No invented employer emails.
5. **Recruiter emails:** OEM account email is notified on apply / accept / interview / success / fail. Interview time is stored and shown in the CRM inbox.

Cal digest (#155) was not reverted. Process 03 stays CRM. Signup wall stays. Hermes stays retired.

## Tests

- pytest `tests/test_jobs_crm_keep_apply.py` + `tests/test_jobs_crm_recruiter.py` — 13 passed
- vitest `jobsCrmAccount.test.ts` + `jobsWorkflow.test.ts` — 36 passed
- Local Vite `:3000` canary: `/` and `/pipeline?src=jobs_activate` 200; served `jobsCrmAccount.ts` has `next=offer` + `#jobs-next-steps`

## Leftovers

- **Fly:** `alembic upgrade head` for `rcrt0a1b2c3d4` (docs + tokens). Until then uploads/tokens 500 on production API.
- **Resend:** OEM + employer sends need `RESEND_API_KEY` / `RESEND_FROM_EMAIL`. Inbound MX still not wired.
- **Disk:** specs live under `uploads/jobs_crm/` on the API host (ephemeral on Fly unless a volume is mounted).
- Draft PR + Vercel frontend deploy after merge. Do not merge until agent-verify is green and JS contains `Keep these` / `next=offer#jobs-next-steps`.

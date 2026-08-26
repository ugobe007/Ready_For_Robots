# Outcome — Keep jobs, apply, employer inbox

**Date:** 2026-08-26  
**Branch:** `cursor/crm-keep-apply-009b`

## What shipped

Authenticated Keep jobs upserts Job Cards onto the user account. Next steps collects robot name, catalogued OEM SKUs, skippable PoC, and the user’s proposed monthly price. Apply stores `job_applications` and sends outreach only when a real employer email exists. Employer replies live in `application_messages` on the CRM desk (thread + Reply + paste-inbound).

## Schema

- `user_kept_jobs` — user_id, job_key, employer/work identity, payload, robot/submission, TTL/acted_at
- `job_applications` — offer snapshot, send_status, reply_token, thread_state
- `application_messages` — inbound/outbound body, from/to, provider_id
- `jobs_crm_activity` — account pipeline activity (graduates `rfr_pipeline_activity_v1`)

Migration: `jkep0a1b2c3d4` (revises `osku0a1b2c3d4`).

## How the loop works

1. **Keep jobs** (Job Cards or CRM) → POST `/api/jobs-crm/keep` when signed in; unsigned still writes handoff and hits the wall.
2. Status bar: “N jobs saved”. CRM link only when not already on `/pipeline?src=jobs_activate`.
3. **Next steps** → form on the desk (`?next=offer` or after keep). Apply gated on price + catalogued model.
4. **Apply** → persist offer. Send via existing Resend (`send_email_via_resend`) if a real employer email is on the card. Otherwise `not_sent_no_email` and a clear reason. No invented contacts. No invented rental dollars.
5. **Inbox** on the kept job: thread state, Reply (Resend), paste-inbound fallback.

## Email

Outbound uses `RESEND_API_KEY` + `RESEND_FROM_EMAIL`. Reply-To is `jobs+{token}@` (or SCOUT/RESEND reply domain). Inbound webhook `/api/webhooks/resend/inbound` now matches `job_applications.reply_token`.

## Leftovers (do not treat as shipped)

- `alembic upgrade head` on Fly — not deployed this cycle.
- Resend inbound MX/DNS for `jobs+token@` — without it, automatic employer replies will not arrive. Desk paste + outbound reply still work.

## Tests

- `/workspace/venv/bin/python -m pytest tests/test_jobs_crm_keep_apply.py tests/test_plan_entitlements.py` — 25 passed
- `pnpm --dir readyforrobots-new exec vitest run` jobsCrmAccount + jobsWorkflow + jobsApply + pstackSite — 48 passed

## Product constraints held

Wall stays. Step 03 stays CRM. No SIGNAL hop. No invented employer emails. Monthly price labeled as the user’s proposed offer.

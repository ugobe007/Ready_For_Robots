# Outcome — Jobs CRM interview hold

**Date:** 2026-08-27  
**Branch:** `cursor/crm-interview-hold-009b`  
**PR:** parent opens (ManagePullRequest not in this agent’s tool catalog). Push: `origin/cursor/crm-interview-hold-009b`.  
**Base:** `origin/main` includes #156 (`68b77518`).

## Hold vs propose

| Path | Status | What is stored | Who locks it | Email |
|------|--------|----------------|--------------|-------|
| **Propose time** | `interview_scheduled` | `interview_at` only. No hold columns. | OEM **Confirm interview** | OEM status + both-sides if employer email exists |
| **Connect us** | `interview_requested` | `interview_mode=connect_you` | OEM arranges, then confirm | Same; no time |
| **Hold this slot** | `interview_held` | `slot_start` / `slot_end` / `held_at` / `hold_expires_at` (48h) / `interview_at=slot_start` | OEM **Confirm hold** (books) or **Release hold** (clears). Until then the hold *is* the booked window. | OEM “slot held for {employer} {job} {time}” + `/oem-hold/:token`. Both-sides only with a real employer email. |

`/calendar` is SIGNAL Cal. Interviews do not enter that send queue. `CAL_AUTONOMY_ENABLED` stays `0`. Hermes stays retired. No invented employer emails. No HOT-buyer send.

## Schema (`job_applications`)

Alembic `ihld0a1b2c3d4` (revises `rcrt0a1b2c3d4`):

- `held_at`
- `hold_expires_at`
- `slot_start`
- `slot_end`
- `oem_hold_token` (unique; OEM confirm/release link)

Status value: `interview_held`. Mode: `hold_slot`. Success/fail still `POST .../outcome`.

## Surfaces

- `/employer/:token` — Propose time **or** Hold this slot (offered windows + custom range)
- `/oem-hold/:token` — OEM confirm / release from the recruiter email
- CRM inbox (`/pipeline?src=jobs_activate`) — held window + Confirm hold / Release hold

## Tests

```
PYTHONPATH=/workspace /workspace/venv/bin/pytest tests/test_jobs_crm_recruiter.py tests/test_jobs_crm_keep_apply.py -q
# 19 passed

pnpm exec vitest run client/src/lib/jobsCrmAccount.test.ts
# 4 passed
```

Hold vs propose, token confirm, no both-sides send without employer email, mocked Resend.

## Leftovers

- Fly `alembic upgrade` for `ihld0a1b2c3d4` (needed before hold columns exist in prod).
- Hold expiry is stored, not auto-released by cron.
- Inbound MX still leftover so employer replies may need paste.
- No browser drive of `/employer/:token` (needs a live token + API).

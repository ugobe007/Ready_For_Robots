# Jobs CRM

Jobs CRM is step 03: keep checked Job Cards in native CRM as 3 unlocked job opportunities on free. It is not the SIGNAL buyer pipeline.

## Sub-features

- `crm-activate` Next from the job list goes to `/crm?src=jobs_activate`.
- `crm-unlock` signed-in free users see 3 unlocked jobs from the handoff. Unlocked rows carry the same model `list_line` as QUALIFY (layer · time · who trains).
- `crm-auth` signed-out users hit signup/login with Jobs `src`, then return to CRM.
- `crm-watch` optional watch when work changes (email) — do not require it for a pass.

## How to get to it (user POV)

- Click `Next →` on the job list (process bar, list top, page footer).
- Open header CRM while on Jobs chrome.
- After signup from Jobs, land on `/crm?src=jobs_activate`.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.
- Unlocked job list requires a session. Without it, report `verified-unreachable` — do not pass via `/pipeline`.

- **URL.** `python3 scripts/agent_verify.py drive --feature jobs-crm --evidence "$EVIDENCE"`. Homepage JS contains `jobs_activate` and `/crm`. The activate URL returns 200 (SPA).
- **Session path (browser, when signed in).** Open `/crm?src=jobs_activate`. Headline CRM. Three unlocked jobs. No “Back to pipeline”.
- **Signed-out.** Signup/login, not Pipeline. `src=jobs_activate` survives the auth hop.
- **Proof.** `drive-jobs-crm.json`. If `unlocked_jobs_visible` is false, the JSON must name the session prerequisite.

## Gotchas

- Bare `/crm` is SIGNAL CRM and may show Pipeline. Jobs verify uses `src=jobs_activate` only.
- Do not treat a login wall as 3 unlocked jobs.
- Do not create accounts in CI.

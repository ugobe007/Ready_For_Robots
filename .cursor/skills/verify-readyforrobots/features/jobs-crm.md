# Jobs CRM

Jobs CRM is step 03: kept Job Cards land on the desk at `/pipeline?src=jobs_activate` (5 on free). Apply to jobs rectifies credentials (pack, PoC, monthly rental you will charge) and tracks follow-up. It is not the SIGNAL buyer pipeline and not an OEM shortlist.

## Sub-features

- `crm-activate` Next from the job list goes to `/pipeline?src=jobs_activate`.
- `crm-unlock` free users see 5 unlocked jobs from the handoff. Rows carry the same model `list_line` as QUALIFY.
- `crm-apply` Apply panel: credential gaps, outreach draft, workflow strategy. Apply is disabled until gaps close. Status: blocked → ready → applied → follow-up.
- `crm-auth` signed-out users hit signup/login with Jobs `src`, then return to the desk.
- `crm-watch` optional watch when work changes (email) — do not require it for a pass.

## How to get to it (user POV)

- Click `Next →` on the job list (process bar, list top, page footer). All five example jobs start Keep-checked.
- Open header CRM while on Jobs chrome.
- After signup from Jobs, land on `/pipeline?src=jobs_activate`.
- Bookmarks to `/crm?src=jobs_activate` redirect to the same desk.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.
- Unlocked job list requires a Jobs handoff snapshot (and usually a session). Without jobs in the snapshot, report `verified-unreachable` — do not pass via SIGNAL `/pipeline`.

- **URL.** `python3 scripts/agent_verify.py drive --feature jobs-crm --evidence "$EVIDENCE"`. Homepage JS contains `jobs_activate` and `/pipeline`. The activate URL returns 200 (SPA).
- **Session path (browser, when signed in).** Open `/pipeline?src=jobs_activate`. Headline CRM. Up to five jobs. No Hermes OEM vendor list. No SIGNAL buyer feed.
- **Signed-out.** Signup/login, not SIGNAL Pipeline. `src=jobs_activate` survives the auth hop.
- **Proof.** `drive-jobs-crm.json`. If `unlocked_jobs_visible` is false, the JSON must name the session/snapshot prerequisite.

## Gotchas

- Bare `/crm` and bare `/pipeline` are SIGNAL and may show Pipeline nav. Jobs verify uses `src=jobs_activate` only.
- Do not treat a login wall as 5 unlocked jobs.
- Do not create accounts in CI.
- Do not invent a monthly rental on the Apply panel.

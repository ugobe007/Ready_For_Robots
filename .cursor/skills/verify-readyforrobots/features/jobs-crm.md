# Jobs CRM

Step 03 is **CRM**. Checking a job on step 02 dumps it into this desk. Kept Job Cards land on `/pipeline?src=jobs_activate` (5 on free). Place this job (quote the rental) is the money action *inside* CRM. It is not the SIGNAL buyer pipeline and not an OEM shortlist.

## Sub-features

- `crm-activate` Open CRM from the job list uses `jobsCrmOpenHref`. Signed-out users hit `/signup?next=/pipeline?src=jobs_activate`.
- `crm-unlock` free users see 5 unlocked jobs from the handoff after signup (checks dump live).
- `crm-place` Headline **CRM**. Process bar 03 current. One next action (Confirm pack → Lock this quote → Place this job). Apply is disabled until pack, PoC, and a user-entered monthly rental are in.
- `crm-auth` signed-out users cannot use the desk; a direct `/pipeline?src=jobs_activate` hit redirects through signup.

## How to get to it (user POV)

- Click `Open CRM →` on the job list. All five example jobs start Keep-checked. Signed-out users sign up, then land on the desk.
- Open header **CRM** on Jobs chrome (visible signed out; click hits the wall).
- After signup from Jobs, land on `/pipeline?src=jobs_activate`.
- Bookmarks to `/crm?src=jobs_activate` redirect to the same desk.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.
- Unlocked job list requires a Jobs handoff snapshot. Without jobs in the snapshot, report `verified-unreachable` — do not pass via SIGNAL `/pipeline`.

- **URL.** `python3 scripts/agent_verify.py drive --feature jobs-crm --evidence "$EVIDENCE"`. Homepage JS contains `jobs_activate` and `/pipeline`.
- **Session path (browser).** Open `/pipeline?src=jobs_activate` with a handoff. Headline **CRM**. Process bar 03 current. Up to five employer chips. No Hermes OEM list. No SIGNAL buyer feed.
- **Proof.** `drive-jobs-crm.json`.

## Gotchas

- Bare `/crm` and bare `/pipeline` are SIGNAL.
- Do not invent a monthly rental.
- Do not treat a login wall as 5 placed jobs.
- The signup wall in front of the desk is required. Spec: `docs/jobs_crm.md`.

# Jobs CRM

Step 03 is **CRM**. Checking a job on step 02 dumps it into this desk. Kept Job Cards land on `/pipeline?src=jobs_activate` (5 on free). Place this job (quote the rental) is the money action *inside* CRM. It is not the SIGNAL buyer pipeline and not an OEM shortlist.

## Sub-features

- `crm-activate` Open CRM from the job list goes to `/pipeline?src=jobs_activate` without a signup wall.
- `crm-unlock` free users see 5 unlocked jobs from the handoff (checks dump live).
- `crm-place` Headline **CRM**. Process bar 03 current. One next action (Confirm pack → Lock this quote → Place this job). Apply is disabled until pack, PoC, and a user-entered monthly rental are in.
- `crm-auth` signed-out users see the desk first; signup is a keep-this-desk link.

## How to get to it (user POV)

- Click `Open CRM →` on the job list. All five example jobs start Keep-checked and are already in CRM.
- Open header **CRM** on Jobs chrome (signed in or out).
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

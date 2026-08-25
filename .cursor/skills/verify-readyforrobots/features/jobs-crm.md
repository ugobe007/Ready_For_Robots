# Jobs CRM

Step 03 is **Place** — the money moment. Kept Job Cards land on `/pipeline?src=jobs_activate` (5 on free). The desk names what we know, your next move (pack → quote → apply), and tracks follow-up. It is not the SIGNAL buyer pipeline and not an OEM shortlist.

## Sub-features

- `crm-activate` Next from the job list goes to `/pipeline?src=jobs_activate`.
- `crm-unlock` free users see 5 unlocked jobs from the handoff.
- `crm-place` Punchline: Place {robot}. Process bar 01/02/03 continues. Agent brief + Pack/Quote/Apply lanes. Apply is disabled until pack, PoC, and a user-entered monthly rental are in.
- `crm-auth` signed-out users hit signup/login with Jobs `src`, then return to the desk.

## How to get to it (user POV)

- Click `Next →` on the job list. All five example jobs start Keep-checked.
- Open header CRM while on Jobs chrome.
- After signup from Jobs, land on `/pipeline?src=jobs_activate`.
- Bookmarks to `/crm?src=jobs_activate` redirect to the same desk.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor healthy.
- Unlocked job list requires a Jobs handoff snapshot. Without jobs in the snapshot, report `verified-unreachable` — do not pass via SIGNAL `/pipeline`.

- **URL.** `python3 scripts/agent_verify.py drive --feature jobs-crm --evidence "$EVIDENCE"`. Homepage JS contains `jobs_activate` and `/pipeline`.
- **Session path (browser).** Open `/pipeline?src=jobs_activate` with a handoff. Headline **Place**. Process bar 03 current. Up to five employer chips. No Hermes OEM list. No SIGNAL buyer feed.
- **Proof.** `drive-jobs-crm.json`.

## Gotchas

- Bare `/crm` and bare `/pipeline` are SIGNAL.
- Do not invent a monthly rental.
- Do not treat a login wall as 5 placed jobs.

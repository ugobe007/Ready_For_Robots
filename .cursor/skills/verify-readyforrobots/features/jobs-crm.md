# Jobs CRM

Step 03 is **CRM**. Checking a job on step 02 dumps it into this desk. Kept Job Cards land on `/pipeline?src=jobs_activate` (5 on free) as a **collected listing**. Expand to inspect, then Place this job (quote the rental) when ready. It is not the SIGNAL buyer pipeline and not an OEM shortlist.

## Sub-features

- `crm-activate` Open CRM from the job list uses `jobsCrmOpenHref`. Signed-out users hit `/signup?next=/pipeline?src=jobs_activate`.
- `crm-unlock` free users see 5 unlocked jobs from the handoff after signup (checks dump live). One keep prompt: Keep N jobs? Confirmation: Yes, keep them.
- `crm-place` Headline **CRM**. Process bar 03 current. Default view is the expandable listing. Place / pack / quote is the second beat on an opened egg. Quote lock needs a user-entered monthly rental. PoC is preferred and skippable.
- `crm-auth` signed-out users cannot use the desk; a direct `/pipeline?src=jobs_activate` hit redirects through signup.
- `crm-pstack` release gate, not desk chrome. Matcher owns the jobs. Signup wall stays. Do not render JOBS AGENT PROTOCOL on the CRM desk.

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
- **Session path (browser).** Open `/pipeline?src=jobs_activate` with a handoff. Headline **CRM**. Process bar 03 current. Listing of collected jobs (not a forced single-job form). Employer names emerald. Keep N jobs? then Yes, keep them, then Apply (`next=offer#jobs-next-steps`). Expand inspects employer / workplace / work. Place is the second beat. No Hermes OEM list. No SIGNAL buyer feed.
- **Unsigned.** Direct desk URL still redirects through signup. Do not treat the wall as 5 placed jobs.
- **Proof.** `drive-jobs-crm.json`.

## Gotchas

- Bare `/crm` and bare `/pipeline` are SIGNAL.
- Do not invent a monthly rental.
- Do not block quote lock or Place on empty PoC.
- Do not treat a login wall as 5 placed jobs.
- The signup wall in front of the desk is required. Spec: `docs/jobs_crm.md`.

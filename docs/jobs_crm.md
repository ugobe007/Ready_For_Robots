# Jobs CRM — product spec and feature list

Canonical spec for native CRM on the Jobs path. Agents must follow this file instead of improvising CRM from chat.

**Charter:** [value_first_principle.md](value_first_principle.md) · [robot_employment_model.md](robot_employment_model.md) · [EXPERIMENT_MODE.md](EXPERIMENT_MODE.md) · [CAPABILITY_MODEL.md](CAPABILITY_MODEL.md)

**Unit of value:** a **Robot Job** (named employer + real work). Native CRM is where those jobs live after FIND. A sale is an outcome of **placement**, not the object we optimize.

---

## Job to be done

A robot OEM or integrator registers a robot, sees Job Cards, and keeps matching jobs in **one desk** so they can pack, quote rental, apply, and follow up — without hopping to SIGNAL buyers or a third-party CRM first.

If native CRM is not **intuitive**, users revert to HubSpot. Export exists so they can leave; the product wins when they do not need to.

---

## Workflow (locked)

```
FIND (URL) → QUALIFY (Job Cards, anonymous OK) → signup wall → CRM desk
```

| Step | Surface | Auth | What the user sees |
|------|---------|------|--------------------|
| 01 FIND | `/` | Anonymous | Robot URL → understood robot |
| 02 QUALIFY | `/` results | Anonymous | Job Cards. Value is proven **here**. |
| — wall | `/signup?next=/pipeline?src=jobs_activate&src=jobs_activate` | Required | Account before the desk. |
| 03 CRM | `/pipeline?src=jobs_activate` | Signed in | Collected jobs as an expandable **listing**. Place this job lives **inside** an opened egg, not as the only screen. |

Process bar CTA after results: **`Open CRM →`**. That CTA always runs `jobsCrmOpenHref(signedIn, submissionId)` — never a raw desk URL for signed-out users.

**Do not** rename step 03 to Place, Pipeline, or Activate in chrome. Place is the money action **on a deal**, not the process step.

---

## Why the signup wall exists

Value-first forbids a wall **in front of Job Cards**. It does **not** forbid a wall **in front of the CRM desk**.

Unsigned users may:

- paste a URL
- see Job Cards
- Keep-check jobs (handoff is written locally)

Unsigned users may **not**:

- land on `/pipeline?src=jobs_activate` as a working desk
- persist jobs to an account CRM
- Place / apply / export as if they had an account

A direct `/pipeline?src=jobs_activate` hit while signed out **redirects through signup**. Do not “fix” that by showing the desk unsigned.

---

## Free vs paid (Jobs CRM entitlements)

Server source of truth: `app/services/plan_entitlements.py` (`JOBS_CRM_FREE_*`). Client mirrors: `CRM_UNLOCKED_JOBS` / `CRM_FREE_*` in `jobsWorkflow.ts`.

| Rule | Free | Paid |
|------|------|------|
| Jobs shown on the desk per FIND dump | **5** (Keep-checked first) | All jobs that match the registered robot(s) |
| FIND dumps that persist per calendar month | **3** (5 + 5 + 5 = **15** jobs) | Unlimited matching jobs |
| Time to act | **7 days** per dumped batch. Un-acted jobs drop. | No 7-day drop |
| What “act” means | Apply / Place this job (pack → quote rental → apply) on that job | Same actions, no expiry |
| Robot OEM / SIGNAL rows on this desk | **Never** | **Never** |
| Reply / follow-up on matching jobs | Only the 5 currently unlocked, while they live | All matching jobs |

**Force compliance (free only):** if the user does not apply within 7 days, those five jobs leave the desk so they can run a new FIND (up to three times in the month). We do not keep a graveyard of ignored free leads.

**Paid:** do not enforce the 5-cap, the 15/month cap, or the 7-day TTL. Paid users access and reply to every job that matches their robots.

**Honesty:** do not render 7-day / 15-month meters in the UI until the **server** expires rows and counts monthly dumps. Constants + this spec land first; enforcement is a follow-up mission.

---

## Feature list

### F1 — Signup wall (ship)

`jobsCrmOpenHref(signedIn, submissionId)`:

- signed in → `/pipeline?src=jobs_activate` (optional `&submission=`)
- signed out → `/signup?next=<desk>&src=jobs_activate`

Wire this in: process CTA, header CRM on Jobs chrome, handoff “Open CRM”, and an unsigned desk redirect.

Unsigned `/pipeline?src=jobs_activate` still redirects through signup. The wall is **not** a dead end: process chrome (01 FIND / 02 Job Cards / 03 CRM) and a **Sign up to open CRM →** next stay visible. Header Jobs / About stay on screen. Do not show the working desk unsigned.

### F2 — Dump checked jobs into CRM (ship)

Keep-check writes `rfr_jobs_handoff_v1` immediately. After signup, the desk hydrates from that handoff (plus `?submission=`). The user does not re-check jobs on the desk.

### F3 — Desk is jobs, not OEMs (ship)

`/pipeline?src=jobs_activate` renders **JobsCrmDesk** only. No SIGNAL, no robot-OEM directory, no HOT-buyer hop. Header CRM on this src stays on the desk.

### F4 — Five-job free unlock (ship, display)

Free desk lists at most `CRM_UNLOCKED_JOBS` (5) from the dump. Copy must not claim a larger unlock than the API grants.

### F5 — Place this job inside CRM (ship)

Primary deal action on an **opened** collected job: **Place this job →** (pack → quote rental → apply). Not a fourth process-bar step. Not the default screen. Monthly rental is required to lock a quote. PoC is preferred and skippable.

### F5a — Collect then act (ship)

Default desk is a **listing** of collected jobs (cap 5 on free). Select-all keeps all five. Expanding a row inspects the Job Card (employer, workplace, work, qualification, open questions, task-model burden). Place / pack / quote is the second beat. Acting on one job does not deselect the others.

### F6 — Pipeline activity on the same job record (ship, local)

Actions taken on FIND / QUALIFY (keep, Open CRM) and on the desk (Place, apply) append to a **pipeline activity** log on the job’s CRM record so the user can review them later. v1 may be `localStorage` keyed per browser; account persistence is next. Collect / inspect / place language on the desk maps onto these same events. Do not add points or badges.

### F7 — 7-day free TTL + 15/month (spec now, enforce next)

See table above. Server expires un-acted free jobs at 7 days and rejects a fourth FIND dump in the month.

### F8 — Paid: all matching jobs, no TTL (spec now, enforce next)

Paid plan skips F7 caps. Desk lists every job that matches the user’s registered robots; they may reply to all of them.

### F9 — Export to the user’s CRM (spec now, ship next)

Users may export **Robot Job** leads (not SIGNAL companies) to HubSpot or CSV. Export is an escape hatch. Native CRM must stay easier than exporting.

---

## Intuitive CRM (non-negotiable UX)

The desk must feel like **keeping work**, not like being marched through a gate.

Hunt on FIND. Collect on the CRM listing. Enjoy Place this job when the user is ready.

| Do | Do not |
|----|--------|
| One listing of jobs the user already checked, expandable for details | A forced single-job action form as the first screen |
| Select-all / keep all 5 collected jobs; acting on one leaves the others selected | Chip-as-single-active (“one job or nothing”) |
| Employer names in emerald display type (`text-emerald-400`) | Employer names as body copy |
| Activity on each job (“Kept from FIND”, “Opened CRM”, “Placed”) | A second product (SIGNAL) pretending to be CRM |
| Place this job on an inspected egg, after peruse | Rename the process step to Place and hide CRM |
| Honest “employers prefer proof of concept”; skip is allowed | Block quote lock / Place because PoC is empty |
| Light collect / inspect / hatch copy (N of 5 eggs in the basket) | Points, badges, 7-day meters before the API enforces them, invented rental dollars |
| Signup copy: save these jobs to your CRM | Signup copy: unlock HOT buyers / Cal / analytics |
| Export as a quiet action | Force HubSpot as the only way to keep jobs |
| Header CRM visible on Jobs chrome; click hits the wall if signed out | Hide CRM until after signup (users will not find the desk) |
| Process bar + leave-desk next on the wall and the signed desk | A CRM page with no next step and no navigation links |

---

## Routes and helpers

| Helper | File | Role |
|--------|------|------|
| `jobsActivateHref` | `jobsWorkflow.ts` | Desk URL |
| `jobsSignupHref` | `jobsWorkflow.ts` | `/signup?next=&src=` |
| `jobsCrmOpenHref` | `jobsWorkflow.ts` | **Only** CTA/header/handoff/unsigned-desk entry |
| `jobsCrmNextHref` / `jobsCrmLeaveHref` | `jobsWorkflow.ts` | Wall next = signup; signed next = Job Cards (`/?restore=1`) or FIND (`/?new=1`) |
| `JobsProcessChrome` | `JobsProcessChrome.tsx` | 01 / 02 / 03 + next on CRM wall and desk |
| `jobsForCrmDesk` | `jobsWorkflow.ts` | Checked-first, cap 5 |
| `crmSelectAllKeys` / `crmCollectedCountLabel` | `jobsWorkflow.ts` | Keep all collected jobs; basket count |
| `canLockQuote` | `jobsApply.ts` | Monthly rental required. PoC not required. |
| `jobs_crm_unlocked_limit` | `plan_entitlements.py` | Server 5 vs unlimited |
| `JOBS_CRM_FREE_*` | `plan_entitlements.py` | Batch 5, 3×/month, TTL 7 |

---

## Agent rules (stop the rewire)

1. **Never remove the signup wall** in front of the CRM desk.
2. **Never put a signup wall in front of Job Cards** (step 02).
3. **Never hop** Jobs CRM to SIGNAL, robot OEMs, or `/pipeline` without `src=jobs_activate`.
4. **Never rename** process step 03 away from **CRM**.
5. **Never invent** rental economics on the card; Place this job is the quote path.
6. **Never claim** 7-day / 15-month limits in UI before the API enforces them.
7. **Never require** PoC evidence to lock a quote or Place this job. Prefer it; allow skip.
8. **Never remount FIND while researching.** One Start jobs click = one match. Do not `location.assign` / `reload` / `/?new=1` bounce, and do not require SIGNAL `.pipeline-detail-shell` on `/`.
9. Change this file (and tests) if the workflow changes — do not “fix” CRM from a one-line chat prompt.
10. Site agents follow pstack How / Act / Critic. Do not replace the matcher with an LLM. Do not remove the signup wall.
11. Never render Jobs CRM (`/pipeline?src=jobs_activate` or `/crm?src=jobs_*`) without process chrome and a next step.

---

## Out of scope (this spec still names them)

Matcher retune, Cal, invented dollars, HubSpot OAuth export UI, cron expiry job, paid “all matching jobs” query beyond the current dump.

## Next missions (ranked)

1. Persist pipeline activity + dumped jobs on the **account** (not only `localStorage`).
2. Enforce F7 on the API (TTL + monthly dump count).
3. Paid F8: list all matching jobs, not only the last FIND dump.
4. F9: HubSpot + CSV export of Robot Jobs.

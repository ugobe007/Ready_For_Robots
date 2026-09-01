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
| 02 QUALIFY | `/` results | Anonymous | Process chrome: **Available jobs**. Job Cards. Value is proven **here**. |
| — wall | `/signup?next=/pipeline?src=jobs_activate&src=jobs_activate` | Required | Account before the desk. |
| 03 CRM | `/pipeline?src=jobs_activate` | Signed in | Jobs they kept as an expandable **listing**. Place this job lives **inside** an opened job, not as the only screen. |

Process bar: **01 Show us your robot → 02 Available jobs → 03 CRM**. Step 02 action is **Open CRM →**. Apply is not a sibling CTA on that screen. Signed CRM desk still uses **Apply to jobs →** (violet, not neon green). Open CRM still uses `jobsCrmOpenHref(signedIn, submissionId)` — never a raw desk URL for signed-out users.

**Do not** rename step 03 to Place, Pipeline, or Activate in chrome. Place is the money action **on a deal**, not the process step. Step 02 chrome is **Available jobs** (renamed from “Here are its jobs”).

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

Primary deal action on an **opened** job: **Place this job →** (pack → quote rental → apply). Not a fourth process-bar step. Not the default screen. Monthly rental is required to lock a quote. PoC is preferred and skippable.

### F5a — Collect then act (ship)

Default desk is a **listing** of jobs the user kept (cap 5 on free). Checking on Available jobs dumps the row; the desk hydrates that handoff after signup. Expanding a row inspects the Job Card. Place / pack / quote stays the second beat on an opened job. Acting on one job does not deselect the others. Do not restore **Keep N jobs?** / **Yes, keep them**. Do not add a **Select all N** control.

### F6 — Pipeline activity on the same job record (ship, account)

Actions taken on FIND / QUALIFY (keep, Open CRM) and on the desk (Place, apply) append to an activity log on the job’s CRM record so the user can review them later. Signed-in activity is stored on the account (`jobs_crm_activity`). `rfr_pipeline_activity_v1` remains a local bridge for unsigned handoff. Desk copy maps onto these same events. Do not add points or badges.

### F10 — Keep jobs on the account (ship)

Authenticated keep upserts selected Job Cards onto the user (`user_kept_jobs`). N is the selected/kept count, not a hardcoded 5 when they kept 3. Schema: user, job identity (employer, work title, source ids), robot/submission, timestamps, free TTL/entitlement. Unsigned users still hit the wall; after signup, kept jobs restore. Status bar says "N jobs saved". Off the desk the bar links to CRM; on the desk it links to **Apply to jobs**. Apply copy: apply. We draft. You review and send.

Each kept job asks **Do you have a model for this work?** The OEM names the model source (product, vendor, or known policy) or says they will train it for the job. Stored on `user_kept_jobs.work_task_model_kind` / `work_task_model_source`. Unknown until they answer. Do not invent a model name. **Cal** asks this on the desk after Open CRM if it is still blank.

### F11 — Next steps offer → apply outreach (ship)

After keep, **Apply to jobs** / **Next steps** is a real control: `/pipeline?src=jobs_activate&next=offer#jobs-next-steps`. The form collects robot name, catalogued OEM SKUs, skippable PoC (written note plus optional async video URL: Loom / YouTube / Vimeo embed, Google Drive as a link-out), why they are applying, attached specs, and the **user’s proposed monthly price**. Prepare looks for a public YouTube clip of the robot (company + SKU). Empty video URL does not block apply. `POST /api/jobs-crm/apply` and `/apply-selected` store a **prepared** draft (`status=prepared`). The operator reviews subject, body, video, and contacts, then sends. `POST /api/jobs-crm/applications/{id}/send` is the only employer send. No invented emails. No auto-email. No Google Meet. No invented rental dollars. Do not skip the offer form. Do not accept video files on the specs upload path. YouTube: Data API when `YOUTUBE_API_KEY` is set; otherwise a documented search URL. Fail empty over the wrong robot’s video.

### F12 — Employer inbox on the desk (ship)

Employer replies live in `application_messages` (inbound/outbound). The CRM desk shows thread state (sent / awaiting reply / replied), interview time, and a Reply composer. If inbound MX is not wired, users can paste a reply. Access is on the kept job — not a sidecar spreadsheet.

### F13 — Brochure / spec upload (ship)

Signed-in OEM uploads PDF/image specs (`user_robot_documents`, 8 MB, account-private). Selected docs attach via `application_documents` and appear on the offer snapshot. Outreach includes hosted token URLs (Resend attachments when small). Not a public unauthenticated dump.

### F14 — Employer evaluate (ship)

Outreach (only with a real employer email) includes token **Accept**, **Set up interview**, and **Decline**. `/employer/:token` needs no RFR account. The public payload includes `poc_video_url` when the OEM pasted an allowlisted link; the page embeds Loom/YouTube/Vimeo or shows **Watch demo**. Tokens write `application_messages` and status (`accepted` / `interview_requested` / `interview_scheduled` / `interview_held` / `declined`). Decline requires a task-model reason code (`work_mismatch` / `model_unproven` / `site_constraints` / `timing_budget` / `other`) plus optional note (`other` requires a note). Scheduling is **propose a time** (OEM confirms), **hold this slot** (concrete window persisted on the application), or paste a meeting URL. Empty meeting URL is **we schedule with the employer** — not Cal, not Google Meet. `/calendar` is SIGNAL and stays unwired.

### F16 — Product presentation (ship, queue)

After Job Cards (never in front of FIND): **Build a product presentation**. Requires **sign up and pay**. Provider interface (Manus / Replit / ChatGPT) is config-backed. No API key → queue the request; never fake a finished deck.

### F17 — Apply selected jobs (ship)

Click-to-apply the Job Cards the user kept. `POST /api/jobs-crm/apply-selected` prepares one offer on every selected card (`prepared` until the operator sends). Recruiter follow-up is the existing employer-email path after send. Scheduling is paste/hold meeting URL or the honest “we schedule with the employer” state.

### F15 — Recruiter emails to the OEM (ship)

On apply, accept, decline, interview, hold, confirm/release, and success/fail, email the signed-in OEM account. Confirm job + employer + status. A decline email names the reason code (why the robot/policy did not fit) and any note. A hold email names the employer, job, and held window, plus a confirm/release link (`/oem-hold/:token`). Both-sides interview email sends only when a real employer email exists. Interview time lives on the application.

### F7 — 7-day free TTL + 15/month (spec now, enforce next)

See table above. Server expires un-acted free jobs at 7 days and rejects a fourth FIND dump in the month.

### F8 — Paid: all matching jobs, no TTL (spec now, enforce next)

Paid plan skips F7 caps. Desk lists every job that matches the user’s registered robots; they may reply to all of them.

### F9 — Export to the user’s CRM (spec now, ship next)

Users may export **Robot Job** leads (not SIGNAL companies) to HubSpot or CSV. Export is an escape hatch. Native CRM must stay easier than exporting.

---

## Intuitive CRM (non-negotiable UX)

The desk must feel like **keeping work**, not like being marched through a gate.

Hunt on FIND. Keep jobs on the CRM listing. Apply when the user is ready.

| Do | Do not |
|----|--------|
| One listing of jobs the user already kept, expandable for details | A forced single-job action form as the first screen |
| Jobs you kept, then Apply; acting on one leaves the others selected. Do not restore **Keep N jobs?** / **Yes, keep them** | Dual Keep all 5 / Select all N / Keep jobs buttons that ask the same question |
| Employer names in emerald display type (`text-emerald-400`) | Employer names as body copy |
| Activity on each job (“Kept from FIND”, “Opened CRM”, “Placed”) | A second product (SIGNAL) pretending to be CRM |
| Place this job on an opened job, after peruse | Rename the process step to Place and hide CRM |
| Honest “employers prefer proof of concept”; skip is allowed | Block quote lock / Place because PoC is empty |
| Spoken recruiter copy that names the robot (`Jobs for TUG`) | Protocol, pstack, egg/collect, “we discover real jobs… real decision makers,” JOBS AGENT PROTOCOL |
| Signup copy: keep these jobs on your desk | Signup copy: unlock HOT buyers / Cal / analytics |
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
| `jobsCrmOfferHref` | `jobsCrmAccount.ts` | Desk Apply / Next steps → `?next=offer#jobs-next-steps` |
| `JobsProcessChrome` | `JobsProcessChrome.tsx` | 01 / 02 / 03 + next on CRM wall and desk |
| `jobsForCrmDesk` | `jobsWorkflow.ts` | Checked-first, cap 5 |
| `keepTheseJobsPrompt` / `crmSelectAllKeys` | `jobsWorkflow.ts` | Unused keep-prompt helper (do not restore in UI); default-select helper (no Select all button) |
| `canLockQuote` | `jobsApply.ts` | Monthly rental required. PoC not required. |
| `jobs_crm_unlocked_limit` | `plan_entitlements.py` | Server 5 vs unlimited |
| `JOBS_CRM_FREE_*` | `plan_entitlements.py` | Batch 5, 3×/month, TTL 7 |

---

### F18 — Cal on the desk (ship)

After Open CRM, **Cal** is the Jobs recruiter on `/pipeline?src=jobs_activate`. He reads kept Job Cards, asks missing apply facts (task-model source vs self-train, catalogued SKU, monthly rental, skippable PoC), and prepares the existing violet apply draft. The operator reviews and sends. Tools: `GET/POST /api/jobs-crm/cal/desk`. Production `CAL_AUTONOMY_ENABLED=0`. Not FIND. Not buyer/SIGNAL mail. Not a second home.

---

## Agent rules (stop the rewire)

1. **Never remove the signup wall** in front of the CRM desk.
2. **Never put a signup wall in front of Job Cards** (step 02).
3. **Never hop** Jobs CRM to SIGNAL, robot OEMs, or `/pipeline` without `src=jobs_activate`.
4. **Never rename** process step 03 away from **CRM**.
5. **Never invent** rental economics on the card; Place this job is the quote path.
6. **Never claim** 7-day / 15-month limits in UI before the API enforces them.
7. **Never require** PoC evidence to lock a quote or Place this job. Prefer it; allow skip.
8. **Never remount FIND while researching.** One Find jobs click = one match. Do not `location.assign` / `reload` / `/?new=1` bounce, and do not require SIGNAL `.pipeline-detail-shell` on `/`.
9. Change this file (and tests) if the workflow changes — do not “fix” CRM from a one-line chat prompt.
10. Site agents follow pstack How / Act / Critic. Do not replace the matcher with an LLM. Do not remove the signup wall.
11. Never render Jobs CRM (`/pipeline?src=jobs_activate` or `/crm?src=jobs_*`) without process chrome and a next step.

---

## Out of scope (this spec still names them)

Matcher retune, invented dollars, HubSpot OAuth export UI, cron expiry job, paid “all matching jobs” query beyond the current dump. Cal-as-core / FIND chatbot / buyer autonomy stay out of scope.

## Next missions (ranked)

1. Wire Resend inbound MX/DNS so employer replies land automatically (`jobs+{token}@` domain).
2. Enforce F7 cron expiry job in production (`alembic upgrade` leftover until Fly runs it). Alembic `edcl0a1b2c3d4` adds `job_applications.decline_reason_code` + `decline_note` (revises `pvud0a1b2c3d4`). Fly migrate may timeout; employer Decline needs those columns in prod.
3. **Job contacts:** Alembic `jcnt0a1b2c3d4` adds `robot_jobs.employer_email` / `contact_url` / `apply_url`. Fly leftover: `alembic upgrade head`. Until then apply send stays off for live jobs that only have JSONB contacts if the column write was skipped. New scrapes extract page-only mailboxes; posting HTML is not stored so the 1,664 existing rows cannot be backfilled from disk.
4. Paid F8: list all matching jobs, not only the last FIND dump.
5. F9: HubSpot + CSV export of Robot Jobs.

# Landing chrome wiring (after #213)

**Date:** 2026-09-02
**Type:** build
**Branch:** `cursor/landing-link-wiring-009b` from `origin/main` @ `ecace835` (merged #213)
**Draft PR:** parent opens vs `main` (ManagePullRequest was not in this agent catalog). Compare: https://github.com/ugobe007/Ready_For_Robots/pull/new/cursor/landing-link-wiring-009b

Do not Fly. Do not merge #195. Leftover #202 stays closed — do not reopen.

## Product routes (kept)

| Visit | Dest |
|---|---|
| Kare landing | `/` or `/?new=1` — **Put your robot to work.** |
| OEM FIND step 1 | `/?visit=jobs` — URL + I know the robot |
| Employer MATCH step 1 | `/?visit=candidates` |
| FIND timeout | stays on `/?visit=jobs` (no bounce to landing) |
| Open CRM | `/pipeline?src=jobs_activate` (signup wall if unsigned) |
| Cal | signed Jobs CRM desk only |
| About **Find jobs →** | FIND (`/?visit=jobs`), not SIGNAL |
| Wordmark | `/?new=1` landing is OK; FIND errors do not go to landing |

`restore=1` is FIND (`landingVisitFromSearch("?restore=1") === "jobs"`), not the fork.

## Link map (label → dest)

| Label | Dest |
|---|---|
| Wordmark | `/?new=1` |
| Header Jobs (landing `/` or `/?new=1`) | `/?new=1` |
| Header Jobs (FIND / MATCH) | `/?visit=jobs` |
| Header Jobs (About / Pricing / Privacy / other Jobs chrome) | `/?visit=jobs` |
| Header Jobs (Jobs CRM desk) | `/?visit=jobs&restore=1` |
| Header About | `/intelligence` |
| Header CRM (unsigned) | `/signup?next=%2Fpipeline%3Fsrc%3Djobs_activate&src=jobs_activate` |
| Header CRM (signed Jobs chrome) | `/pipeline?src=jobs_activate` |
| Sign In | `/login?next=` current path+search |
| Look for robot jobs (hero door) | `/?visit=jobs` |
| Look for robot candidates (hero door) | `/?visit=candidates` |
| How Jobs works 01 / 02 | `/?visit=jobs` |
| How Jobs works 03 Open CRM → | CRM wall (same signup URL) |
| Start free workspace | CRM wall |
| Download the 2026 briefing | `/intelligence#report` |
| Footer Pricing | `/pricing` |
| Footer FAQ | `/pricing#faq` |
| Footer Privacy | `/privacy` |
| support@readyforrobots.com | `mailto:support@readyforrobots.com` |
| About **Find jobs →** | `/?visit=jobs` |
| About **Keep jobs in CRM** | CRM wall |
| About **Download report** | `#report` (in-page on About) |
| Compare **Find jobs →** | `/?visit=jobs` |
| Compare **Keep jobs in CRM** | CRM wall |
| MATCH **Looking for jobs instead?** | `/?visit=jobs` |
| Privacy Home | `/?new=1` |
| Privacy Find jobs | `/?visit=jobs` |
| Pricing free CTA | CRM wall |
| Pricing **Look for robot jobs** | `/?visit=jobs` |
| Process 01 on Jobs CRM | `/?visit=jobs` |
| Process 02 | restore FIND (`/?visit=jobs&restore=1`) |
| Process 03 / Open CRM | `jobsCrmOpenHref` |

Doors are real `<a href>`. How steps are real links. No `#` hrefs on landing.

## What I changed

Canonical frontend: `readyforrobots-new/client/`.

- `jobsLanding.ts` — `restore=1` → visit jobs; How steps carry `href`/`cta`; `LANDING_LINK_MAP` + footer dests (`/pricing`, `/pricing#faq`, `/privacy`, mailto, `/intelligence#report`).
- `jobsWorkflow.ts` — `jobsHeaderJobsHref`: landing stays landing, FIND/MATCH/About/Pricing → FIND, CRM desk → restore. `showJobsSiteChrome` includes `/pricing` and `/privacy`.
- `JobsLanding.tsx` — hero doors + How/brief CTAs are anchors.
- `ExperimentHeader.tsx` — Jobs uses `jobsHeaderJobsHref`; intercept only when the href is landing; Sign In returns to current path+search.
- `JobsProcessChrome.tsx` — step 01 is `jobsFindHref()` imported from `jobsLanding` (not `jobsFreshHomeHref` / not a missing export).
- `EmployerMatchWorkspace.tsx` — “Looking for jobs instead?” is `<a href={jobsFindHref()}>`.
- `Intelligence.tsx` / `Compare.tsx` — Find jobs → FIND; Keep jobs in CRM → CRM wall.
- `SiteFooter.tsx` — Start free workspace → `jobsCrmOpenHref(false)`.
- `Pricing.tsx` / `Privacy.tsx` — Jobs `ExperimentHeader`, no SIGNAL Pipeline nav; Pricing free CTA → CRM wall; FAQ is `/pricing#faq`.
- `signupWorkflowPath.ts` — `src=jobs_activate` with empty next → `/pipeline?src=jobs_activate`.

## Tests

Vitest click-path / href tests in `jobsLanding.test.ts` (“cannot swap visits”) plus restore/header/chrome/signup tests in `jobsWorkflow.test.ts` and `signupWorkflowPath.test.ts`. 82 passed on those files earlier this run.

Browser (Vite `http://127.0.0.1:3003/`, CDP):

- Landing `/` — headline **Put your robot to work.** Doors: jobs → FIND form + I know the robot; candidates → employer MATCH (no FIND form). Landing hashes: none.
- Header from landing: Jobs `/?new=1`, About `/intelligence`, CRM signup wall.
- About **Find jobs →** → `/?visit=jobs` FIND form, not landing.
- Header CRM → unsigned signup wall `next=/pipeline?src=jobs_activate`.
- Pricing uses Jobs chrome (JOBS/ABOUT/CRM, no Pipeline); `#faq` exists.
- FIND header Jobs stays on `/?visit=jobs` (no bounce to landing).
- MATCH “jobs instead” → `/?visit=jobs`.
- Footer Pricing / FAQ / Privacy / mailto as mapped.
- Privacy Home → landing; Find jobs → FIND.

Drive log: `/opt/cursor/artifacts/landing_wiring_drive.json` and `landing_wiring_about.json`.

## Remaining stubs (honest, not `#`)

- Brief job cards (Amazon / Benchmark / Whitsons) still expand in-place; CTA goes to FIND, not a per-job page.
- About **Download report** is in-page `#report` on `/intelligence`.
- Pricing Pro / Premium still Stripe / SIGNAL-ish feature lists under Jobs chrome (Free copy is Jobs-honest).
- Privacy legal copy still mentions sales-intelligence language.
- About / Pricing / signup `SiteFooter` still lists existing SIGNAL leftover routes (`/find-robots`, `/compare`, `/integrations`, `/robots`, `/newsletter`, `/vendor/design`). Those are real pages, not `#`. Landing footer does not include them.
- Cal stays off landing / MATCH / FIND.
- No Fly; production will not show this until a frontend deploy.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195. Do not reopen #202.

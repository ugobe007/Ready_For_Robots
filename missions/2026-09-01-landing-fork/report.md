# Landing fork report

**Date:** 2026-09-01
**Branch:** `cursor/landing-fork-jobs-candidates-009b`
**Verdict:** two options on `/`. FIND after option 1. Employer MATCH then post. pstack critic PASS. No Fly.

This is the report. You do not need a terminal to read it.

Rule held: MATCH named catalog robots. Never company → category → jobs. Value first: Job Cards / named robots before signup.

## Routing

| Visit | URL | Step 1 |
|-------|-----|--------|
| Who is this visit | `/` or `/?new=1` | Look for robot jobs / Look for robot candidates |
| OEM FIND | `/?visit=jobs` | Paste URL, or pick class / named catalog SKU |
| Employer MATCH | `/?visit=candidates` | Work tiles + optional description / job URL |

## Option 1. Look for robot jobs

Local Vite `/?visit=jobs`. URL form and I know the robot both present.

Pasted `https://www.dexory.com/`. Identity is DexoryView on dexory.com. Class picker when the page is not enough. Same FIND backend.

Serving class lists Bear Servi, Keenon, Pudu BellaBot. Click BellaBot. Job Cards: "Jobs for BellaBot", Open CRM. Five example jobs, checked.

## Option 2. Look for robot candidates

Serving MATCH (local API): 12 named catalog robots. BellaBot, Dinerbot, HolaBot, KettyBot, PuduBot 2, Scotty, Servi. Vendors from the catalog (Pudu, Pringle, Keenon, Richtech, Bear). No invented SKU.

Mining MATCH: empty. Copy: "No catalog robots for this work yet. Post the job so OEMs can find it."

Post-job draft after matches. Employer Harborview Dining, title Table service and bussing. Shortlist kept on the device. Persist needs Fly/DB. We did not invent a contact.

## Critic

`PYTHONPATH=. python3 scripts/pstack_release.py` ok.

Dexmate FIND matches. Greenfield is GREENFIELD ROBOTICS, not strawberry. Diligent live class is healthcare, 11 named employer jobs, not humanoid empty.

## Files

- `readyforrobots-new/client/src/pages/Jobs.tsx`
- `readyforrobots-new/client/src/components/JobsLanding.tsx`
- `readyforrobots-new/client/src/components/EmployerMatchWorkspace.tsx`
- `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` (I know the robot)
- `app/api/employer_jobs.py`
- `app/services/employer_robot_match.py`
- `docs/feature_map.md`

## Not deployed

No Fly on this branch. Employer MATCH is new API. FIND URL still works on Fly. Draft PR. Do not merge #195.

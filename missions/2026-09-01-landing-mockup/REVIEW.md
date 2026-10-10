# Landing mockup: Put your robot to work.

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/landing-fork-copy-009b` and `cursor/put-robot-to-work-22f6`  
**#209** merged 20:58 UTC with mockup headline A still on `/`. Operator copy is the three commits after that merge. ManagePullRequest was not in this agent catalog, so a new draft PR was not opened here.  
**Mockup layout:** https://rfr70sui-wipjpxme.manus.space  
**Copy:** operator (wins over mockup headline A)  
**Did not** merge #195. **Did not** Fly-deploy. Cal stays off `/`.

## Operator copy (source of truth)

**Headline.** Put your robot to work.

**Subhead.** Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM.

**Look for robot jobs.** Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess — and match it to real jobs.

**Look for robot candidates.** Tell us the work. We match named catalog robots from the ontology. Then you can post the job.

Mockup layout stays. Mockup headline A ("Robots need jobs. We find the work.") does not ship. Operator line was picker D in the A–E chrome. The picker is not in production.

## Routing

`/` and `/?new=1` are the landing fork. Doors go to `/?visit=jobs` (FIND step 1) and `/?visit=candidates` (employer step 1). No Cal. No invented SKUs.

## Layout kept from the mockup

Navy `#0A0F1E`, mint `#2EE6A8`. Two door cards, How Jobs works, jobs brief, vocabulary, Start free workspace, slim footer.

## Verify

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts`: 5 passed. Headline assertion is Put your robot to work. Mockup A is rejected.

`PYTHONPATH=. python3 scripts/pstack_release.py --local`: How / Act / Critic ok. FIND drive skipped.

Local Vite `http://127.0.0.1:3000/`:

- H1 is Put your robot to work.
- Subhead is the operator CRM sentence.
- Old lines are gone: Who is this visit?, Jobs for robots. Robots for jobs., Robots need jobs. We find the work.
- No Headline options picker. No Cal.
- Look for robot jobs / Look for robot candidates still have short explainers.

Screenshot: `/opt/cursor/artifacts/landing_put_your_robot_to_work.png`

Stay draft on the follow-up PR. No Fly. #209 already merged with mockup A. Compare: https://github.com/ugobe007/Ready_For_Robots/compare/main...cursor/put-robot-to-work-22f6

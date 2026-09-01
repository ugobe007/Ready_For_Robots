# Landing mockup: Put your robot to work.

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/landing-fork-copy-009b` (draft #209)  
**Mockup layout:** https://rfr70sui-wipjpxme.manus.space  
**Copy:** operator (wins over mockup headline A)  
**Did not** merge #195. **Did not** Fly-deploy. Cal stays off `/`.

## Operator copy (source of truth)

**Headline.** Put your robot to work.

**Subhead.** Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM.

**Look for robot jobs.** Paste a product URL, or pick a named catalog robot. We read the SKU — not a category guess — and match it to real jobs.

**Look for robot candidates.** Tell us the work. We match named catalog robots from the ontology. Then you can post the job.

Mockup layout stays. Mockup headline A ("Robots need jobs. We find the work.") does not ship. That was picker D in the mockup; the operator sent it as the line.

## Routing

`/` and `/?new=1` are the landing fork. Doors go to `/?visit=jobs` (FIND step 1) and `/?visit=candidates` (employer step 1). No Cal. No invented SKUs.

## Layout kept from the mockup

Navy `#0A0F1E`, mint `#2EE6A8`. Two door cards, How Jobs works, jobs brief, vocabulary, Start free workspace, slim footer.

## Verify

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts`  
`PYTHONPATH=. python3 scripts/pstack_release.py --local`  
Local Vite `http://127.0.0.1:3000/`: H1 is Put your robot to work. Old Who is this visit? and Jobs for robots. Robots for jobs. are gone.

Stay draft. No Fly.

# Landing copy: product, not visitor

**Date:** 2026-09-01
**Type:** build
**Branch:** `cursor/landing-fork-copy-009b` from `origin/main` @ `b7ae3959` (#208 already on main)

Copy only on `/`. Routing stays `/?visit=jobs` and `/?visit=candidates`. No Cal on the landing. Did not merge #195. Did not Fly-deploy.

## Copy

**Headline.** Jobs for robots. Robots for jobs.

**Subhead.** You have a robot or you have work, and we show matches before you sign up.

**Look for robot jobs.** You have a robot. Paste a product URL or pick from the catalog, and we show openings it can do.

**Look for robot candidates.** You have work. We show named robots that can do it, then you can post the job.

Emerald accent stays on the sentence-starting Jobs / Robots, same chrome as FIND.

## Why this, not the old line

"Who is this visit?" asked the user a process question. Recruiter copy names the product. The subhead names the two people and the value (matches before signup). Each card says what the click does.

## Files

- `readyforrobots-new/client/src/lib/jobsLanding.ts`
- `readyforrobots-new/client/src/components/JobsLanding.tsx`
- `readyforrobots-new/client/src/lib/jobsLanding.test.ts`
- `docs/feature_map.md`

## Verify

Vitest landing fork. Local Vite: landing, Look for robot jobs → FIND step 1, Look for robot candidates → employer step 1, wordmark back to the fork.

`python3 scripts/pstack_release.py --local` How / Act. Stay draft. No Fly.

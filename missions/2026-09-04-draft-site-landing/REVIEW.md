# Draft site landing PR

**Date:** 2026-09-04
**Type:** build
**Branch:** `cursor/draft-site-landing-5072`
**PR:** cherry-picked the five post-#216 commits from `cursor/kare-apple-type-009b`

Do not Fly. Stay draft. Do not merge #195.

## How

Landing chrome: `JobsLanding.tsx`, `jobsLanding.ts`, `index.css` `.rfr-landing`.
FIND type path: `RobotJobsWorkspace.tsx` FindRail.
Matcher stays `POST /api/robot-job-match`. FIND submit stays `POST /api/robot-job-search`.

## What changed

Those drafts were on Fly as `git-dev` and never got a PR after #216 merged.

- Headline **Put Robots to Work.** Emerald on **Robots** and the Kare face.
- Intro **Submit your robot URL or your robot job. We put robots to work.**
- Ghost doors with more space. Brief heading **Jobs for robots.**
- FIND heading **Jobs for robots.** Step 1 catalog is **What type of robot?** then **Find jobs →**.

## Tests

`pnpm exec vitest run` jobsLanding + jobsWorkflow + pstackSite + pstackRelease + robotClassOptions: 58 passed.

`pytest` class_picker + pstack: 30 passed.

`python3 scripts/pstack_release.py --local` How / Act / Critic ok.

`python3 scripts/pstack_release.py` How / Act / Critic ok. Dexmate 200 `matches` identity Dexmate. Greenfield 200 `qualify_robot` identity GREENFIELD ROBOTICS. Diligent `robot_class=healthcare`, 12 named employer jobs.

Browser (Vite `http://127.0.0.1:3020/`):

- `/` Put Robots to Work, emerald Kare, intro, two ghost doors, Jobs for robots brief.
- Jobs for Robots → `/?visit=jobs` FIND form + What type of robot? dropdown.
- Serving class find stayed on FIND. Empty-type copy can still show while the live tape lists jobs (corpus, not a bounce).
- Robots for Jobs → `/?visit=candidates` employer MATCH.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195.

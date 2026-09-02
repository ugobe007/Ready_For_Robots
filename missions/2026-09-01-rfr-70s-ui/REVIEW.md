# Port Kare Macintosh landing onto `/`

**Date:** 2026-09-01
**Type:** build
**Branch:** `cursor/rfr-70s-ui-apply-009b` from `origin/main` + `docs/rfr-70s-ui-source` on `origin/cursor/rfr-70s-ui-source-009b`
**Did not** Fly-deploy. **Did not** merge #195. **Did not** reuse #212 as the landing.

## Verdict

Ported. Source folder is on `origin/cursor/rfr-70s-ui-source-009b` as a nested Manus app (`docs/rfr-70s-ui-source/rfr-70s-ui-source/`). `App.tsx` there mounts `Home.tsx` (dark navy + Kare Macintosh). That is what landed on `/`.

#212 (`cursor/rfr-70s-ui-port-009b`) was the missing-folder note. This branch is the apply. Merged `origin/main` so #210 copy, #211 FIND stay + employer MATCH, and #212's report stay on history without replacing the port.

## What was ported

Visual language from `Home.tsx`:

- EB Garamond headlines, Silkscreen labels
- Navy `#0A0F1E` / `#0D1426` / `#111A30`, mint `#2EE6A8`
- 50% dither fills, window-chrome title bars, 3px offset shadows
- Instant invert CTAs (no easing)
- 1-bit pixel robot, briefcase, document, hand

Product copy and routing stayed:

- Headline: **Put your robot to work.**
- Sub: Jobs for a robot you already have, or robots for work you need done. Paste a product URL — we match it to real jobs, then keep them in our CRM.
- Look for robot jobs → `/?visit=jobs`
- Look for robot candidates → `/?visit=candidates`

Headline picker A–E stayed out. Cal stayed off landing. Brief cards still name Amazon / Benchmark / Whitsons with robot classes, not invented SKUs. No Apollo. Hunter.io not added.

FIND after the jobs door is still Jobs chrome (`RobotJobsWorkspace`). Only `/` got the Kare skin.

## FIND timeout and employer MATCH (from main)

`origin/main` now includes #211:

- Timeout / 500 / abort keep `/?visit=jobs`
- `ensureFindStayVisit` + Jobs.tsx visit guard
- Identity timeout 8s, search timeout 12s
- Employer MATCH catalog snapshot + JD upload (`catalog_only`)

Cal desk types from #205 (`CalDeskTurnBody` and the rest) stay on main. They are not on the landing.

## Proof

- `pnpm exec vitest run` jobsLanding + findResearch + pstackSite + pstackRelease + jobsWorkflow: **62 passed**
- `pytest` agent_verify / pstack / employer_robot_match / healthcare: **40 passed**
- `python3 scripts/pstack_release.py --local`: How / Act / Critic ok. `find_no_home` green.
- Browser on local Vite `http://127.0.0.1:3000/`:
  - `/` shows the Kare landing, operator headline, both doors
  - Jobs door → FIND (`aria-label="Find jobs for your robot"`), not a bounce to `/`
  - Candidates door → employer MATCH
  - No Cal desk, no Apollo, no headline picker
  - Screenshots: `/opt/cursor/artifacts/landing_kare_desktop.png`, `landing_kare_mobile.png`, `landing_door_jobs_find.png`, `landing_door_candidates.png`

## Gaps

- Nested Manus tree (server, shadcn dump, Mainframe / Help Wanted / Space-Age routes) is not copied into this PR. Visual source stays on `cursor/rfr-70s-ui-source-009b`.
- ExperimentHeader is still the product bar (Jobs / About / CRM / Sign in). The mockup's duplicate header was not stacked on top.
- FIND and employer MATCH keep current Jobs chrome. They are not Kare windows.
- No Fly. Production HTML will not show this until a frontend deploy.

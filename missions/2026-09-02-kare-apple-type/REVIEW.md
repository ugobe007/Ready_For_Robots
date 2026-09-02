# Sparse System 1 landing on `/`

**Date:** 2026-09-02
**Type:** build
**Branch:** `cursor/kare-apple-type-009b` (extends sibling ChicagoFLF commits `7244ab7d` / `cbbd6cfe`)
**Draft PR:** `gh pr create` is not writable here (GraphQL createPullRequest denied). Compare: https://github.com/ugobe007/Ready_For_Robots/pull/new/cursor/kare-apple-type-009b

Do not Fly. Do not merge #195.

## How

Landing chrome lives in `readyforrobots-new/client/` (`JobsLanding.tsx`, `jobsLanding.ts`, `index.css` `.rfr-landing`). FIND after **Jobs for Robots** stays `/?visit=jobs`. Employer **Robots for Jobs** stays `/?visit=candidates`. Matcher stays `POST /api/robot-job-match` in `app/services/robot_job_capability_match.py`. This PR does not add a second matcher and does not put protocol chrome on `/`.

## What changed

Canonical frontend: `readyforrobots-new/client/`.

Landing chrome only. Matcher, FIND submit, and CRM wall are untouched. FIND and employer MATCH keep current Jobs chrome.

**Layout.** Sparse fork from the white mock, on navy/cream/mint. Kicker **Ready For Robots · Jobs** (Jobs in mint). Two-line Chicago headline **Put your robot to work.** Cream, not mint. Subhead Archivo: **Find jobs for robots and find robots for jobs.** Mint square with the navy Kare face. Two text doors, not cards: **Jobs for Robots** / **Robots for Jobs**. Quiet hairline footer. No how-it-works grid, jobs brief accordion, vocabulary tiles, or briefing CTA.

**Type.** ChicagoFLF stays the System 1 face. Subhead stays Archivo. Silkscreen and Press Start stay off.

**Not SIGNAL.** No Market Intelligence report hero, no emerald newsletter, no robot index dashboard. White in the mock is layout air, not the color system.

**Not Flintstone.** No dither fills, no window bars, no 2px offset shadows, no invert CTAs.

## Tests

`pnpm exec vitest run` jobsLanding + jobsWorkflow + pstackSite + pstackRelease: 52 passed.

`python3 scripts/pstack_release.py --local` How / Act / Critic ok.

`python3 scripts/pstack_release.py` How / Act / Critic ok. Dexmate FIND 200 `matches` identity Dexmate. Greenfield 200 `qualify_robot` identity GREENFIELD ROBOTICS, not strawberry. Diligent live `robot_class=healthcare`, 12 named employer jobs.

Browser (Vite `http://127.0.0.1:3020/`):

- `/` cream Chicago headline, Archivo subhead, mint Kare square, two text doors. No Market Intelligence, no newsletter, no window bars.
- Jobs for Robots → `/?visit=jobs` FIND form (`aria-label="Find jobs for your robot"`) + I know the robot. Landing copy gone.
- Robots for Jobs → `/?visit=candidates` employer MATCH (What is the work). No FIND form.

Drive log: `/opt/cursor/artifacts/landing_sparse_chicago_drive.json`
Screenshots: `landing_sparse_chicago_desktop.png`, `landing_sparse_chicago_mobile.png`, `landing_door_jobs_find.png`, `landing_door_candidates.png`.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195.

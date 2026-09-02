# Kare landing: System 1 Chicago type, not arcade chunk

**Date:** 2026-09-02
**Type:** build
**Branch:** `cursor/kare-apple-type-009b` from `origin/main` @ `77275700` (merged #215)
**Draft PR:** `gh pr create` is not writable here (GraphQL createPullRequest denied). ManagePullRequest is not in this agent catalog. Compare: https://github.com/ugobe007/Ready_For_Robots/pull/new/cursor/kare-apple-type-009b

Do not Fly. Do not merge #195.

## How

Landing type lives in `readyforrobots-new/client/` (`index.css` `.rfr-landing`, `JobsLanding.tsx`, `jobsLanding.ts`). FIND after Look for robot jobs stays `/?visit=jobs`. Matcher stays `POST /api/robot-job-match` in `app/services/robot_job_capability_match.py`. This PR does not add a second matcher.

`docs/rfr-70s-ui-source` is still on `origin/cursor/rfr-70s-ui-source-009b`. That mockup used EB Garamond plus Silkscreen. Neither is the System 1 face. We vendored ChicagoFLF instead.

## What changed

Canonical frontend: `readyforrobots-new/client/`.

Landing chrome only. Matcher, FIND submit, and CRM wall are untouched.

**Type.** `--font-landing-display` and `--font-landing-ui` are ChicagoFLF (Robin Casady, public domain System 1 Chicago). Files: `client/public/fonts/ChicagoFLF.woff` + `.ttf`. Headline **Put your robot to work.** and both door titles / CTAs compute to `ChicagoFLF, Chicago, Charcoal, sans-serif` at weight 400. Size is Control Panel, not 8-bit marquee: H1 34px, door titles 18px, CTAs 13px mixed case. Subhead stays Archivo. Silkscreen and EB Garamond are off the Google Fonts request. No Press Start.

**Chrome.** Window bars, doors, and CTAs use 1px rules and 2px offset shadows. Dither cell is 2px. Kare face stays (`KARE_FACE`, mint fill). Headline stays cream `#F4EFE4` on navy. Mint is accent only.

**Doors.** Look for robot jobs → `/?visit=jobs`. Look for robot candidates → `/?visit=candidates`.

## Tests

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts` — 8 passed.

`python3 scripts/pstack_release.py` — How / Act / Critic ok. Dexmate and Greenfield FIND drives 200. Diligent live is `healthcare`.

Browser (Vite `http://127.0.0.1:3015/`):

- `/` H1 cream ChicagoFLF 34px / 400. Computed family `ChicagoFLF, Chicago, Charcoal, sans-serif`. Color `rgb(244, 239, 228)`. Subhead Archivo. No Silkscreen on the landing request.
- Jobs door → `/?visit=jobs` FIND form + I know the robot.
- Candidates door → `/?visit=candidates` employer MATCH. No FIND form.

Drive log: `/opt/cursor/artifacts/landing_chicagoflf_drive.json`
Screenshots: `landing_live_silkscreen_before.png` vs `landing_chicagoflf_desktop.png`, `landing_chicagoflf_mobile.png`, `landing_chicagoflf_jobs_find.png`, `landing_chicagoflf_candidates.png`.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195.

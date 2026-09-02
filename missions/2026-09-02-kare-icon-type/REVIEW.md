# Kare landing: our face, 70s type, cream headline, mint accent

**Date:** 2026-09-02
**Type:** build
**Branch:** `cursor/kare-icon-70s-type-009b` from `origin/main` @ `1eb66b09` (merged #214)
**Draft PR:** vs `main` (opened after push).

Do not Fly. Do not merge #195. Leftover #202 stays closed. Do not reopen.

## What changed

Canonical frontend: `readyforrobots-new/client/`.

Landing chrome only. Matcher, FIND submit, and CRM wall are untouched.

**Icon.** Hero / jobs door / footer no longer use the 70s-port 1-bit robot (`LandingPixels` `ROBOT_ROWS`). They use `KARE_FACE` from `kareIcons.ts`, same mark as `ExperimentHeader`. Source bitmap: `readyforrobots-new/client/public/branding/face-icon-reference.png` (15×15). Fill is `FACE_EMERALD` on navy. Employer door still uses the briefcase.

**Type.** `--font-landing-display` is Silkscreen, not EB Garamond. Headline **Put your robot to work.** and both door titles / CTAs (**Look for robot jobs** / **Look for robot candidates**) compute to `Silkscreen, "Courier New", monospace`. Subhead stays Archivo. EB Garamond is off the Google Fonts request.

**Subhead.** **Find jobs for robots and find robots for jobs.** Headline stays **Put your robot to work.**

**Color.** Headline is cream `#F4EFE4` on navy, not mint. Hero wash is paper dither on navy/charcoal. Mint stays accent: CTA invert, featured-door rule, Jobs kicker, and the Kare face.

## Tests

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts` — 8 passed.

`python3 scripts/pstack_release.py` — How / Act / Critic ok. Dexmate and Greenfield FIND drives 200. Diligent live is `healthcare`.

Browser (Vite `http://127.0.0.1:3000/`, CDP):

- `/` headline cream Silkscreen `rgb(244, 239, 228)`. Subhead Archivo. No Garamond link.
- Hero mark is the 15×15 face (225 cells) in the charcoal square.
- Jobs door → `/?visit=jobs` FIND form + I know the robot.
- Candidates door → `/?visit=candidates` employer MATCH. No FIND form.

Drive log: `/opt/cursor/artifacts/landing_kare_icon_type_drive.json`
Screenshots: `landing_kare_face_silkscreen_desktop.png`, `landing_kare_face_silkscreen_mobile.png`.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195. Do not reopen #202.

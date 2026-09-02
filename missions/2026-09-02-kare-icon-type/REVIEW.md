# Kare landing: our face, 70s type, cream headline, mint accent

**Date:** 2026-09-02
**Type:** build
**Branch:** `cursor/kare-icon-70s-type-009b` from `origin/main` @ `1eb66b09` (merged #214)
**Draft PR:** vs `main`.

Do not Fly. Do not merge #195. Leftover #202 stays closed. Do not reopen.

## What changed

Canonical frontend: `readyforrobots-new/client/`.

Landing chrome only. Matcher, FIND submit, and CRM wall are untouched.

**Icon.** Hero / jobs door / footer no longer use the 70s-port 1-bit robot (`LandingPixels` `ROBOT_ROWS`). They use `KARE_FACE` from `kareIcons.ts`, same mark as `ExperimentHeader`. Source bitmap: `readyforrobots-new/client/public/branding/face-icon-reference.png` (15×15). Fill is `FACE_EMERALD` on navy. Employer door still uses the briefcase.

**Type.** `--font-landing-display` is Silkscreen, not EB Garamond. Headline **Put your robot to work.** and both door titles / CTAs (**Look for robot jobs** / **Look for robot candidates**) compute to `Silkscreen, "Courier New", monospace`. Subhead stays Archivo. EB Garamond is off the Google Fonts request.

**Subhead.** Stop word salad. **Find jobs for robots and find robots for jobs.** Headline stays **Put your robot to work.**

**Color.** Headline is cream `#F4EFE4` on navy, not mint. Hero wash is paper dither on navy/charcoal, not green. Panels are navy / charcoal / paper stipple. Mint stays accent only: CTA invert, small rules (featured door, OPEN chip, selected job border), Jobs wordmark / kicker, and the Kare face.

## Tests

`pnpm exec vitest run client/src/lib/jobsLanding.test.ts`

`python3 scripts/pstack_release.py --local` — How / Act / Critic. No Fly.

Browser (local Vite):

- `/` headline cream Silkscreen. Subhead the two-clause line. No Garamond.
- Hero is navy/charcoal, not a green wash. Mint on CTAs and face only.
- Jobs door → `/?visit=jobs` FIND form + I know the robot.
- Candidates door → `/?visit=candidates` employer MATCH.

Screenshots under `/opt/cursor/artifacts/`.

## Do not

Do not Fly-deploy unless asked. Draft PR only. Do not merge #195. Do not reopen #202.

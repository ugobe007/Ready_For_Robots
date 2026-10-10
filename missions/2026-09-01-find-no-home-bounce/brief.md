# FIND timeout must not dump to the landing

**Date:** 2026-09-01  
**Type:** build  
**Agents:** ProductSurface (Act), Deploy (Critic)

## Goal

OEM FIND lookup that hangs ~90s then dumps to the homepage is a break. Stay on FIND step 1 (`/?visit=jobs`) with honest error copy. Fail-fast. Employer MATCH catalog-only. Brighter **I know the robot**. Employer post accepts a JD file. Tests that would have caught the bounce.

## Acceptance

- Timeout / 500 / abort / Failed to fetch never navigate to `/` or `/?new=1`.
- Client identity timeout 8s, composed search 12s, Fly-direct (not Vercel rewrite).
- Employer `POST /api/employer-robot-match` is catalog snapshot only, under 3s after cache.
- JD upload (pdf/docx/txt) persists on `robot_jobs.requirements`.
- `drive --feature find-stay` fails if FIND error returns to landing.
- No Fly unless tests prove a live integrity break. Draft PR. Do not merge #195.
